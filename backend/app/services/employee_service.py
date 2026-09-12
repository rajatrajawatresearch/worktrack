"""Employee management (COMPANY_ADMIN for own company; SUPER_ADMIN any)."""

from sqlalchemy.orm import Session

from app.core import security
from app.core.enums import AuditAction, EmployeeStatus, Role, UserStatus
from app.core.errors import conflict, not_found
from app.models.employee import Employee
from app.models.user import User
from app.repositories import audit_repo, employee_repo, refresh_token_repo, user_repo
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


def create_employee(db: Session, company_id, data: EmployeeCreate, actor: User) -> Employee:
    if employee_repo.get_by_code(db, company_id, data.employee_code):
        raise conflict("This employee code already exists in the company.")
    if user_repo.get_by_email(db, data.email):
        raise conflict("This email is already in use.")

    user = user_repo.create(
        db,
        email=data.email,
        password_hash=security.hash_password(data.password),
        role=Role.EMPLOYEE,
        company_id=company_id,
        phone=data.phone,
    )
    emp = employee_repo.create(
        db,
        user_id=user.id,
        company_id=company_id,
        employee_code=data.employee_code.strip(),
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        phone=data.phone,
        department=data.department,
        designation=data.designation,
        joining_date=data.joining_date,
    )
    audit_repo.create(
        db,
        action=AuditAction.EMPLOYEE_CREATED,
        user_id=actor.id,
        company_id=company_id,
        entity_type="employee",
        entity_id=emp.id,
        meta={"employee_code": emp.employee_code},
    )
    return emp


def get_employee(db: Session, company_id, emp_id, actor: User) -> Employee:
    emp = employee_repo.get(db, emp_id)
    # company_id is None only for SUPER_ADMIN without a company filter (all access).
    if not emp or (company_id is not None and emp.company_id != company_id):
        raise not_found("Employee not found.")
    return emp


def list_employees(db: Session, company_id, *, search, department, status, page, page_size):
    return employee_repo.list_by_company(
        db,
        company_id,
        search=search,
        department=department,
        status=status,
        page=page,
        page_size=page_size,
    )


def update_employee(db: Session, company_id, emp_id, data: EmployeeUpdate, actor: User) -> Employee:
    emp = get_employee(db, company_id, emp_id, actor)
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if value is not None and key == "first_name":
            value = value.strip()
        setattr(emp, key, value)
    # Keep the linked user account status in sync with the employee status.
    if "status" in updates and updates["status"] is not None:
        emp.user.status = (
            UserStatus.ACTIVE if updates["status"] == EmployeeStatus.ACTIVE else UserStatus.INACTIVE
        )
    db.flush()
    audit_repo.create(
        db,
        action=AuditAction.EMPLOYEE_UPDATED,
        user_id=actor.id,
        company_id=emp.company_id,
        entity_type="employee",
        entity_id=emp.id,
        meta=updates,
    )
    return emp


def reset_password(db: Session, company_id, emp_id, new_password: str, actor: User) -> Employee:
    emp = get_employee(db, company_id, emp_id, actor)
    emp.user.password_hash = security.hash_password(new_password)
    # Force re-login everywhere by revoking existing refresh tokens.
    refresh_token_repo.revoke_all_for_user(db, emp.user_id)
    db.flush()
    audit_repo.create(
        db,
        action=AuditAction.PASSWORD_RESET,
        user_id=actor.id,
        company_id=emp.company_id,
        entity_type="employee",
        entity_id=emp.id,
    )
    return emp
