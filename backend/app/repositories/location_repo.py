from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import CompanyStatus
from app.models.company_location import CompanyLocation


def get(db: Session, loc_id) -> CompanyLocation | None:
    return db.get(CompanyLocation, loc_id)


def list_by_company(db: Session, company_id) -> list[CompanyLocation]:
    return list(
        db.scalars(
            select(CompanyLocation)
            .where(CompanyLocation.company_id == company_id)
            .order_by(CompanyLocation.is_primary.desc(), CompanyLocation.created_at.asc())
        ).all()
    )


def primary_for_company(db: Session, company_id) -> CompanyLocation | None:
    loc = db.scalar(
        select(CompanyLocation).where(
            CompanyLocation.company_id == company_id,
            CompanyLocation.is_primary.is_(True),
            CompanyLocation.status == CompanyStatus.ACTIVE,
        )
    )
    if loc:
        return loc
    # Fallback: any active location for the company.
    return db.scalar(
        select(CompanyLocation).where(
            CompanyLocation.company_id == company_id,
            CompanyLocation.status == CompanyStatus.ACTIVE,
        )
    )


def create(db: Session, **kwargs) -> CompanyLocation:
    loc = CompanyLocation(**kwargs)
    db.add(loc)
    db.flush()
    return loc


def clear_primary(db: Session, company_id) -> None:
    for loc in list_by_company(db, company_id):
        if loc.is_primary:
            loc.is_primary = False
    db.flush()
