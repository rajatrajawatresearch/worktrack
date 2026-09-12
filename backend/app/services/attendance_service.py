"""Attendance engine: punch-in/out, breaks, GPS validation, working-time.

Server timestamps are authoritative. All location validation happens here
(the backend is the final authority). The attendance date is the
company-local calendar date.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import AttendanceStatus, AuditAction, BreakType
from app.core.errors import AppError, conflict
from app.core.security import utcnow
from app.models.attendance import Attendance
from app.models.attendance_break import AttendanceBreak
from app.models.company import Company
from app.models.employee import Employee
from app.repositories import attendance_repo, audit_repo, location_repo
from app.schemas.common import LocationPayload
from app.services import geo, time_calc
from app.services.geo import LocationCheck


def company_today(company: Company) -> date:
    try:
        tz = ZoneInfo(company.timezone or settings.DEFAULT_TIMEZONE)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo(settings.DEFAULT_TIMEZONE)
    return datetime.now(tz).date()


def _active_break(att: Attendance) -> AttendanceBreak | None:
    return next((b for b in att.breaks if b.ended_at is None), None)


def _validate_location(db: Session, company: Company, loc: LocationPayload) -> LocationCheck:
    if not geo.coordinates_valid(loc.latitude, loc.longitude):
        raise AppError(
            "INVALID_COORDINATES",
            "The provided GPS coordinates are invalid.",
            422,
            {"latitude": loc.latitude, "longitude": loc.longitude},
        )
    if loc.accuracy is None or loc.accuracy < 0:
        raise AppError("INVALID_COORDINATES", "GPS accuracy is invalid.", 422)

    location = location_repo.primary_for_company(db, company.id)
    if not location:
        raise AppError(
            "NO_COMPANY_LOCATION",
            "No work location is configured for your company. Contact your administrator.",
            422,
        )
    check = geo.check_location(
        loc.latitude,
        loc.longitude,
        loc.accuracy,
        location.latitude,
        location.longitude,
        location.allowed_radius_meters,
        company.max_accuracy_meters,
    )
    if not check.accuracy_ok:
        raise AppError(
            "GPS_ACCURACY_TOO_LOW",
            "Your GPS accuracy is too low. Please move to an open area and try again.",
            422,
            {"accuracy": check.accuracy, "max_accuracy_meters": check.max_accuracy_meters},
        )
    if not check.within_radius:
        raise AppError(
            "OUTSIDE_ATTENDANCE_RADIUS",
            "You are outside the allowed attendance area.",
            422,
            {
                "distance_meters": check.distance_meters,
                "allowed_radius_meters": check.allowed_radius_meters,
            },
        )
    return check


def _audit(db, action, employee, company, att, ip, meta=None):
    audit_repo.create(
        db,
        action=action,
        user_id=employee.user_id,
        company_id=company.id,
        entity_type="attendance",
        entity_id=att.id,
        ip_address=ip,
        meta=meta,
    )


def punch_in(
    db: Session, employee: Employee, company: Company, loc: LocationPayload, ip: str | None = None
) -> tuple[Attendance, LocationCheck]:
    today = company_today(company)
    existing = attendance_repo.get_for_employee_date(db, employee.id, today)
    if existing and existing.status == AttendanceStatus.COMPLETED:
        raise conflict("You have already completed attendance for today.", code="ALREADY_PUNCHED_OUT")
    if existing and existing.punch_in_at is not None and existing.status != AttendanceStatus.ABSENT:
        raise conflict("You are already punched in.", code="ALREADY_PUNCHED_IN")

    check = _validate_location(db, company, loc)
    now = utcnow()
    if existing and existing.status == AttendanceStatus.ABSENT:
        att = existing
        att.punch_in_at = now
        att.punch_in_latitude = loc.latitude
        att.punch_in_longitude = loc.longitude
        att.punch_in_accuracy = loc.accuracy
        att.punch_in_distance_meters = check.distance_meters
        att.status = AttendanceStatus.IN_PROGRESS
        db.flush()
    else:
        att = attendance_repo.create(
            db,
            employee_id=employee.id,
            company_id=company.id,
            attendance_date=today,
            punch_in_at=now,
            punch_in_latitude=loc.latitude,
            punch_in_longitude=loc.longitude,
            punch_in_accuracy=loc.accuracy,
            punch_in_distance_meters=check.distance_meters,
            status=AttendanceStatus.IN_PROGRESS,
        )
    _audit(db, AuditAction.PUNCH_IN, employee, company, att, ip, {"distance_meters": check.distance_meters})
    return att, check


def break_start(
    db: Session, employee: Employee, company: Company, loc: LocationPayload, ip: str | None = None
) -> Attendance:
    att = attendance_repo.get_for_employee_date(db, employee.id, company_today(company))
    if not att or att.punch_in_at is None or att.status == AttendanceStatus.COMPLETED:
        raise conflict("You are not punched in.", code="NOT_PUNCHED_IN")
    if att.status == AttendanceStatus.ON_BREAK or _active_break(att):
        raise conflict("You are already on a break.", code="ALREADY_ON_BREAK")

    check = _validate_location(db, company, loc)
    now = utcnow()
    att.breaks.append(AttendanceBreak(break_type=BreakType.REGULAR, started_at=now))
    att.status = AttendanceStatus.ON_BREAK
    db.flush()
    _audit(db, AuditAction.BREAK_START, employee, company, att, ip)
    return att, check


def break_end(
    db: Session, employee: Employee, company: Company, loc: LocationPayload, ip: str | None = None
) -> Attendance:
    att = attendance_repo.get_for_employee_date(db, employee.id, company_today(company))
    if not att or att.punch_in_at is None or att.status == AttendanceStatus.COMPLETED:
        raise conflict("You are not punched in.", code="NOT_PUNCHED_IN")
    active = _active_break(att)
    if att.status != AttendanceStatus.ON_BREAK or not active:
        raise conflict("You are not currently on a break.", code="NOT_ON_BREAK")

    check = _validate_location(db, company, loc)
    now = utcnow()
    active.ended_at = now
    active.duration_minutes = time_calc.break_duration_minutes(active.started_at, now)
    att.status = AttendanceStatus.IN_PROGRESS
    db.flush()
    _audit(db, AuditAction.BREAK_END, employee, company, att, ip, {"duration_minutes": active.duration_minutes})
    return att, check


def punch_out(
    db: Session, employee: Employee, company: Company, loc: LocationPayload, ip: str | None = None
) -> tuple[Attendance, LocationCheck]:
    att = attendance_repo.get_for_employee_date(db, employee.id, company_today(company))
    if not att or att.punch_in_at is None:
        raise conflict("You are not punched in.", code="NOT_PUNCHED_IN")
    if att.status == AttendanceStatus.COMPLETED:
        raise conflict("You have already punched out.", code="ALREADY_PUNCHED_OUT")
    if att.status == AttendanceStatus.ON_BREAK or _active_break(att):
        raise conflict("Please end your break before punching out.", code="ON_BREAK_CANNOT_PUNCH_OUT")

    check = _validate_location(db, company, loc)
    now = utcnow()
    att.punch_out_at = now
    att.punch_out_latitude = loc.latitude
    att.punch_out_longitude = loc.longitude
    att.punch_out_accuracy = loc.accuracy
    att.punch_out_distance_meters = check.distance_meters
    att.total_work_minutes = time_calc.net_work_minutes(att.punch_in_at, now, att.breaks)
    att.status = AttendanceStatus.COMPLETED
    db.flush()
    _audit(db, AuditAction.PUNCH_OUT, employee, company, att, ip, {"total_work_minutes": att.total_work_minutes})
    return att, check


def get_today(db: Session, employee: Employee, company: Company):
    """Returns (attendance|None, today, status_str, current_work_minutes, on_break, now)."""
    today = company_today(company)
    att = attendance_repo.get_for_employee_date(db, employee.id, today)
    now = utcnow()
    if not att or att.punch_in_at is None:
        return None, today, "NOT_STARTED", 0, False, now
    on_break = _active_break(att) is not None
    if att.status == AttendanceStatus.COMPLETED and att.total_work_minutes is not None:
        current = att.total_work_minutes
    else:
        current = time_calc.current_work_minutes(att.punch_in_at, att.breaks, now)
    return att, today, att.status, current, on_break, now


def current_minutes(att: Attendance, now: datetime | None = None) -> int:
    now = now or utcnow()
    if att.status == AttendanceStatus.COMPLETED and att.total_work_minutes is not None:
        return att.total_work_minutes
    if not att.punch_in_at:
        return 0
    return time_calc.current_work_minutes(att.punch_in_at, att.breaks, now)


def is_on_break(att: Attendance) -> bool:
    return _active_break(att) is not None


def get_history(db, employee, *, date_from, date_to, page, page_size):
    return attendance_repo.history_for_employee(
        db, employee.id, date_from=date_from, date_to=date_to, page=page, page_size=page_size
    )
