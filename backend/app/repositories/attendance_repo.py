from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.attendance import Attendance
from app.models.employee import Employee


def get(db: Session, att_id) -> Attendance | None:
    return db.scalar(
        select(Attendance).options(selectinload(Attendance.breaks)).where(Attendance.id == att_id)
    )


def get_for_employee_date(db: Session, employee_id, att_date: date) -> Attendance | None:
    return db.scalar(
        select(Attendance)
        .options(selectinload(Attendance.breaks))
        .where(Attendance.employee_id == employee_id, Attendance.attendance_date == att_date)
    )


def create(db: Session, **kwargs) -> Attendance:
    att = Attendance(**kwargs)
    db.add(att)
    db.flush()
    return att


def history_for_employee(
    db: Session,
    employee_id,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Attendance], int]:
    stmt = (
        select(Attendance)
        .options(selectinload(Attendance.breaks))
        .where(Attendance.employee_id == employee_id)
    )
    if date_from:
        stmt = stmt.where(Attendance.attendance_date >= date_from)
    if date_to:
        stmt = stmt.where(Attendance.attendance_date <= date_to)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = list(
        db.scalars(
            stmt.order_by(Attendance.attendance_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return rows, total


def _admin_stmt(
    company_id,
    *,
    att_date: date | None = None,
    employee_id=None,
    department: str | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    stmt = (
        select(Attendance)
        .options(selectinload(Attendance.breaks), selectinload(Attendance.employee))
        .where(Attendance.company_id == company_id)
    )
    if att_date:
        stmt = stmt.where(Attendance.attendance_date == att_date)
    if date_from:
        stmt = stmt.where(Attendance.attendance_date >= date_from)
    if date_to:
        stmt = stmt.where(Attendance.attendance_date <= date_to)
    if employee_id:
        stmt = stmt.where(Attendance.employee_id == employee_id)
    if status:
        stmt = stmt.where(Attendance.status == status)
    if department:
        stmt = stmt.join(Employee, Employee.id == Attendance.employee_id).where(
            Employee.department == department
        )
    return stmt


def list_admin(
    db: Session,
    company_id,
    *,
    att_date: date | None = None,
    employee_id=None,
    department: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Attendance], int]:
    stmt = _admin_stmt(
        company_id,
        att_date=att_date,
        employee_id=employee_id,
        department=department,
        status=status,
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = list(
        db.scalars(
            stmt.order_by(Attendance.attendance_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return rows, total


def query_all(
    db: Session,
    company_id,
    *,
    att_date: date | None = None,
    employee_id=None,
    department: str | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[Attendance]:
    """Unpaginated fetch used for CSV/report generation."""
    stmt = _admin_stmt(
        company_id,
        att_date=att_date,
        employee_id=employee_id,
        department=department,
        status=status,
        date_from=date_from,
        date_to=date_to,
    ).order_by(Attendance.attendance_date.asc())
    return list(db.scalars(stmt).all())


def status_counts(db: Session, company_id, att_date: date) -> dict[str, int]:
    stmt = select(Attendance.status, func.count()).where(Attendance.attendance_date == att_date)
    if company_id is not None:
        stmt = stmt.where(Attendance.company_id == company_id)
    rows = db.execute(stmt.group_by(Attendance.status)).all()
    return {status: int(cnt) for status, cnt in rows}


def count_on_date(db: Session, company_id, att_date: date) -> int:
    stmt = select(func.count()).select_from(Attendance).where(Attendance.attendance_date == att_date)
    if company_id is not None:
        stmt = stmt.where(Attendance.company_id == company_id)
    return db.scalar(stmt) or 0
