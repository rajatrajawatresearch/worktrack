from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.employee import Employee
from app.models.user import User


def get(db: Session, emp_id) -> Employee | None:
    return db.get(Employee, emp_id)


def get_by_code(db: Session, company_id, code: str) -> Employee | None:
    return db.scalar(
        select(Employee).where(
            Employee.company_id == company_id, Employee.employee_code == code
        )
    )


def get_by_user(db: Session, user_id) -> Employee | None:
    return db.scalar(
        select(Employee).options(joinedload(Employee.user)).where(Employee.user_id == user_id)
    )


def create(db: Session, **kwargs) -> Employee:
    emp = Employee(**kwargs)
    db.add(emp)
    db.flush()
    return emp


def count_by_company(db: Session, company_id) -> int:
    return (
        db.scalar(select(func.count()).select_from(Employee).where(Employee.company_id == company_id))
        or 0
    )


def count_all(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Employee)) or 0


def list_by_company(
    db: Session,
    company_id,
    *,
    search: str | None = None,
    department: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Employee], int]:
    stmt = (
        select(Employee)
        .options(joinedload(Employee.user))
        .join(User, User.id == Employee.user_id)
        .where(Employee.company_id == company_id)
    )
    if department:
        stmt = stmt.where(Employee.department == department)
    if status:
        stmt = stmt.where(Employee.status == status)
    if search:
        like = f"%{search.lower().strip()}%"
        stmt = stmt.where(
            or_(
                func.lower(Employee.first_name).like(like),
                func.lower(Employee.last_name).like(like),
                func.lower(Employee.employee_code).like(like),
                func.lower(User.email).like(like),
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = list(
        db.scalars(
            stmt.order_by(Employee.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return rows, total
