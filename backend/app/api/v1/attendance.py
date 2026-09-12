import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import AdminScope, EmployeeContext, Pagination, get_client_ip
from app.core.database import get_db
from app.core.enums import Role
from app.core.errors import forbidden, not_found
from app.repositories import attendance_repo
from app.schemas.attendance import AttendanceAdminRow, AttendanceOut, PunchResult, TodayState
from app.schemas.common import LocationInfo, LocationPayload
from app.services import attendance_service, time_calc
from app.utils.responses import paginated, success

router = APIRouter(prefix="/attendance", tags=["attendance"])


def _location_info(check) -> LocationInfo:
    return LocationInfo(
        distance_meters=check.distance_meters,
        allowed_radius_meters=check.allowed_radius_meters,
        accuracy=check.accuracy,
        within_radius=check.within_radius,
    )


def _punch_result(att, check) -> PunchResult:
    return PunchResult(
        attendance=AttendanceOut.model_validate(att),
        location=_location_info(check),
        current_work_minutes=attendance_service.current_minutes(att),
        on_break=attendance_service.is_on_break(att),
    )


# ---- Employee endpoints (static paths declared before /{attendance_id}) ----
@router.get("/today")
def today(ctx: EmployeeContext, db: Session = Depends(get_db)):
    emp, company = ctx
    att, day, status, current, on_break, now = attendance_service.get_today(db, emp, company)
    return success(
        TodayState(
            date=day,
            status=status,
            on_break=on_break,
            current_work_minutes=current,
            server_time=now,
            attendance=AttendanceOut.model_validate(att) if att else None,
        )
    )


@router.post("/punch-in")
def punch_in(payload: LocationPayload, ctx: EmployeeContext, request: Request, db: Session = Depends(get_db)):
    emp, company = ctx
    att, check = attendance_service.punch_in(db, emp, company, payload, ip=get_client_ip(request))
    db.commit()
    return success(_punch_result(att, check))


@router.post("/break/start")
def break_start(payload: LocationPayload, ctx: EmployeeContext, request: Request, db: Session = Depends(get_db)):
    emp, company = ctx
    att, check = attendance_service.break_start(db, emp, company, payload, ip=get_client_ip(request))
    db.commit()
    return success(_punch_result(att, check))


@router.post("/break/end")
def break_end(payload: LocationPayload, ctx: EmployeeContext, request: Request, db: Session = Depends(get_db)):
    emp, company = ctx
    att, check = attendance_service.break_end(db, emp, company, payload, ip=get_client_ip(request))
    db.commit()
    return success(_punch_result(att, check))


@router.post("/punch-out")
def punch_out(payload: LocationPayload, ctx: EmployeeContext, request: Request, db: Session = Depends(get_db)):
    emp, company = ctx
    att, check = attendance_service.punch_out(db, emp, company, payload, ip=get_client_ip(request))
    db.commit()
    return success(_punch_result(att, check))


@router.get("/history")
def history(
    ctx: EmployeeContext,
    pg: Pagination,
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    emp, _company = ctx
    page, page_size = pg
    rows, total = attendance_service.get_history(
        db, emp, date_from=date_from, date_to=date_to, page=page, page_size=page_size
    )
    return paginated(
        [AttendanceOut.model_validate(a) for a in rows],
        page=page,
        page_size=page_size,
        total=total,
    )


# ---- Admin endpoints ----
def _admin_row(att) -> AttendanceAdminRow:
    emp = att.employee
    return AttendanceAdminRow(
        id=att.id,
        employee_id=att.employee_id,
        employee_code=emp.employee_code if emp else "",
        employee_name=emp.full_name if emp else "",
        department=emp.department if emp else None,
        attendance_date=att.attendance_date,
        punch_in_at=att.punch_in_at,
        punch_out_at=att.punch_out_at,
        break_minutes=time_calc.completed_break_minutes(att.breaks),
        total_work_minutes=att.total_work_minutes,
        status=att.status,
    )


@router.get("")
def admin_list(
    scope: AdminScope,
    pg: Pagination,
    att_date: date | None = Query(None, alias="date"),
    employee_id: uuid.UUID | None = Query(None),
    department: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    _user, company_id = scope
    if company_id is None:
        raise not_found("Please select a company (company_id) to view attendance.")
    page, page_size = pg
    rows, total = attendance_repo.list_admin(
        db,
        company_id,
        att_date=att_date,
        employee_id=employee_id,
        department=department,
        status=status,
        page=page,
        page_size=page_size,
    )
    return paginated(
        [_admin_row(a) for a in rows], page=page, page_size=page_size, total=total
    )


@router.get("/{attendance_id}")
def admin_detail(attendance_id: uuid.UUID, scope: AdminScope, db: Session = Depends(get_db)):
    user, company_id = scope
    att = attendance_repo.get(db, attendance_id)
    if not att:
        raise not_found("Attendance record not found.")
    if user.role != Role.SUPER_ADMIN and att.company_id != company_id:
        raise forbidden()
    return success(AttendanceOut.model_validate(att))
