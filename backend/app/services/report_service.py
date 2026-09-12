"""Attendance reports. Generates plain rows + CSV directly (no reporting engine)."""

import csv
import io
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.company import Company
from app.repositories import attendance_repo
from app.services import time_calc

REPORT_TYPES = {"daily", "monthly", "employee", "late", "missing", "hours"}

CSV_FIELDS = [
    "attendance_date",
    "employee_code",
    "employee_name",
    "department",
    "punch_in_at",
    "punch_out_at",
    "break_minutes",
    "total_work_minutes",
    "status",
]


def _tz(company: Company) -> ZoneInfo:
    try:
        return ZoneInfo(company.timezone or settings.DEFAULT_TIMEZONE)
    except ZoneInfoNotFoundError:
        return ZoneInfo(settings.DEFAULT_TIMEZONE)


def _to_local(dt: datetime, tz: ZoneInfo) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(tz)


def _is_late(att, company: Company, tz: ZoneInfo) -> bool:
    if not att.punch_in_at or not company.work_start_time:
        return False
    try:
        hh, mm = company.work_start_time.split(":")
        start = time(int(hh), int(mm))
    except (ValueError, AttributeError):
        return False
    local_in = _to_local(att.punch_in_at, tz)
    threshold = start.hour * 60 + start.minute + (company.late_grace_minutes or 0)
    return (local_in.hour * 60 + local_in.minute) > threshold


def _row(att, tz: ZoneInfo) -> dict:
    emp = att.employee
    return {
        "attendance_date": att.attendance_date.isoformat(),
        "employee_code": emp.employee_code if emp else "",
        "employee_name": emp.full_name if emp else "",
        "department": (emp.department if emp else "") or "",
        "punch_in_at": _to_local(att.punch_in_at, tz).isoformat() if att.punch_in_at else "",
        "punch_out_at": _to_local(att.punch_out_at, tz).isoformat() if att.punch_out_at else "",
        "break_minutes": time_calc.completed_break_minutes(att.breaks),
        "total_work_minutes": att.total_work_minutes if att.total_work_minutes is not None else "",
        "status": att.status,
    }


def build_report(
    db: Session,
    company: Company,
    report_type: str,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    employee_id=None,
) -> list[dict]:
    tz = _tz(company)
    records = attendance_repo.query_all(
        db,
        company.id,
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
    )
    if report_type == "late":
        records = [a for a in records if _is_late(a, company, tz)]
    elif report_type == "missing":
        records = [a for a in records if a.punch_in_at is None or a.punch_out_at is None]
    return [_row(a, tz) for a in records]


def to_csv(rows: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()
