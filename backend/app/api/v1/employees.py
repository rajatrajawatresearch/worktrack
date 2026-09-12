import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AdminScope, Pagination
from app.core.database import get_db
from app.core.errors import bad_request
from app.repositories import attendance_repo
from app.schemas.attendance import AttendanceOut
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeOut,
    EmployeeUpdate,
    ResetPasswordRequest,
)
from app.services import employee_service
from app.utils.responses import paginated, success

router = APIRouter(prefix="/employees", tags=["employees"])


def _require_company(company_id):
    if company_id is None:
        raise bad_request("company_id is required for this operation.")
    return company_id


@router.get("")
def list_employees(
    scope: AdminScope,
    pg: Pagination,
    search: str | None = Query(None),
    department: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    _user, company_id = scope
    company_id = _require_company(company_id)
    page, page_size = pg
    rows, total = employee_service.list_employees(
        db,
        company_id,
        search=search,
        department=department,
        status=status,
        page=page,
        page_size=page_size,
    )
    return paginated(
        [EmployeeOut.model_validate(e) for e in rows], page=page, page_size=page_size, total=total
    )


@router.post("", status_code=201)
def create_employee(payload: EmployeeCreate, scope: AdminScope, db: Session = Depends(get_db)):
    user, company_id = scope
    company_id = _require_company(company_id)
    emp = employee_service.create_employee(db, company_id, payload, user)
    db.commit()
    return success(EmployeeOut.model_validate(emp))


@router.get("/{employee_id}")
def get_employee(employee_id: uuid.UUID, scope: AdminScope, db: Session = Depends(get_db)):
    user, company_id = scope
    emp = employee_service.get_employee(db, company_id, employee_id, user)
    return success(EmployeeOut.model_validate(emp))


@router.patch("/{employee_id}")
def update_employee(
    employee_id: uuid.UUID, payload: EmployeeUpdate, scope: AdminScope, db: Session = Depends(get_db)
):
    user, company_id = scope
    emp = employee_service.update_employee(db, company_id, employee_id, payload, user)
    db.commit()
    return success(EmployeeOut.model_validate(emp))


@router.post("/{employee_id}/reset-password")
def reset_password(
    employee_id: uuid.UUID,
    payload: ResetPasswordRequest,
    scope: AdminScope,
    db: Session = Depends(get_db),
):
    user, company_id = scope
    employee_service.reset_password(db, company_id, employee_id, payload.new_password, user)
    db.commit()
    return success({"reset": True})


@router.get("/{employee_id}/attendance")
def employee_attendance(
    employee_id: uuid.UUID,
    scope: AdminScope,
    pg: Pagination,
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    user, company_id = scope
    emp = employee_service.get_employee(db, company_id, employee_id, user)
    page, page_size = pg
    rows, total = attendance_repo.history_for_employee(
        db, emp.id, date_from=date_from, date_to=date_to, page=page, page_size=page_size
    )
    return paginated(
        [AttendanceOut.model_validate(a) for a in rows], page=page, page_size=page_size, total=total
    )
