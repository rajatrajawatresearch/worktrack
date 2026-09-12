from datetime import date as date_cls
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AdminScope
from app.core.config import settings
from app.core.database import get_db
from app.core.enums import AttendanceStatus
from app.repositories import attendance_repo, company_repo, employee_repo
from app.utils.responses import success

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _default_date(db: Session, company_id) -> date_cls:
    tz_name = settings.DEFAULT_TIMEZONE
    if company_id:
        company = company_repo.get(db, company_id)
        if company and company.timezone:
            tz_name = company.timezone
    try:
        return datetime.now(ZoneInfo(tz_name)).date()
    except ZoneInfoNotFoundError:
        return datetime.now(ZoneInfo(settings.DEFAULT_TIMEZONE)).date()


@router.get("/summary")
def summary(
    scope: AdminScope,
    on_date: date_cls | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
):
    _user, company_id = scope
    if on_date is None:
        on_date = _default_date(db, company_id)

    counts = attendance_repo.status_counts(db, company_id, on_date)
    total_employees = (
        employee_repo.count_by_company(db, company_id)
        if company_id
        else employee_repo.count_all(db)
    )
    in_progress = counts.get(AttendanceStatus.IN_PROGRESS, 0)
    on_break = counts.get(AttendanceStatus.ON_BREAK, 0)
    completed = counts.get(AttendanceStatus.COMPLETED, 0)
    present = in_progress + on_break + completed
    absent = max(0, total_employees - present)
    return success(
        {
            "date": on_date.isoformat(),
            "total_employees": total_employees,
            "present": present,
            "absent": absent,
            "in_progress": in_progress,
            "on_break": on_break,
            "completed": completed,
        }
    )
