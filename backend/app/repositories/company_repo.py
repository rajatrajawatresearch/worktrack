from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.company import Company


def get(db: Session, company_id) -> Company | None:
    return db.get(Company, company_id)


def get_by_code(db: Session, code: str) -> Company | None:
    return db.scalar(select(Company).where(Company.code == code.upper().strip()))


def create(db: Session, **kwargs) -> Company:
    company = Company(**kwargs)
    db.add(company)
    db.flush()
    return company


def list_paginated(db: Session, page: int, page_size: int) -> tuple[list[Company], int]:
    total = db.scalar(select(func.count()).select_from(Company)) or 0
    rows = list(
        db.scalars(
            select(Company)
            .order_by(Company.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return rows, total


def count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Company)) or 0
