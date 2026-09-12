import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import AdminScope, Pagination
from app.core.database import get_db
from app.core.errors import bad_request, not_found
from app.repositories import company_repo
from app.services import report_service
from app.services.report_service import REPORT_TYPES
from app.utils.responses import paginated

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/attendance")
def attendance_report(
    scope: AdminScope,
    pg: Pagination,
    report_type: str = Query("daily", alias="type"),
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    employee_id: uuid.UUID | None = Query(None),
    output: str = Query("json", alias="format"),
    db: Session = Depends(get_db),
):
    _user, company_id = scope
    if company_id is None:
        raise bad_request("company_id is required to generate a report.")
    if report_type not in REPORT_TYPES:
        raise bad_request(f"Invalid report type. Allowed: {sorted(REPORT_TYPES)}")
    company = company_repo.get(db, company_id)
    if not company:
        raise not_found("Company not found.")

    rows = report_service.build_report(
        db,
        company,
        report_type,
        date_from=date_from,
        date_to=date_to,
        employee_id=employee_id,
    )
    if output == "csv":
        csv_text = report_service.to_csv(rows)
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="attendance_{report_type}.csv"'
            },
        )
    page, page_size = pg
    start = (page - 1) * page_size
    return paginated(
        rows[start : start + page_size], page=page, page_size=page_size, total=len(rows)
    )
