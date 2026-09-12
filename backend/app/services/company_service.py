"""Company + location management (SUPER_ADMIN owns; COMPANY_ADMIN reads own)."""

from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.enums import AuditAction, Role
from app.core.errors import conflict, forbidden, not_found
from app.models.company import Company
from app.models.user import User
from app.repositories import audit_repo, company_repo, location_repo, user_repo
from app.schemas.company import CompanyCreate, CompanyUpdate, LocationCreate, LocationUpdate


def create_company(db: Session, data: CompanyCreate, actor: User) -> Company:
    code = data.code.upper().strip()
    if company_repo.get_by_code(db, code):
        raise conflict("A company with this code already exists.")
    if user_repo.get_by_email(db, data.admin_email):
        raise conflict("This admin email is already in use.")

    company = company_repo.create(
        db,
        name=data.name.strip(),
        code=code,
        timezone=data.timezone or settings.DEFAULT_TIMEZONE,
    )
    location_repo.create(
        db,
        company_id=company.id,
        name=data.location.name,
        address=data.location.address,
        latitude=data.location.latitude,
        longitude=data.location.longitude,
        allowed_radius_meters=(
            data.location.allowed_radius_meters or settings.DEFAULT_ALLOWED_RADIUS_METERS
        ),
        is_primary=True,
    )
    user_repo.create(
        db,
        email=data.admin_email,
        password_hash=security.hash_password(data.admin_password),
        role=Role.COMPANY_ADMIN,
        company_id=company.id,
    )
    audit_repo.create(
        db,
        action=AuditAction.COMPANY_CREATED,
        user_id=actor.id,
        company_id=company.id,
        entity_type="company",
        entity_id=company.id,
        meta={"code": company.code, "name": company.name},
    )
    return company


def _get_scoped(db: Session, company_id, actor: User) -> Company:
    company = company_repo.get(db, company_id)
    if not company:
        raise not_found("Company not found.")
    if actor.role != Role.SUPER_ADMIN and actor.company_id != company.id:
        raise forbidden()
    return company


def get_company(db: Session, company_id, actor: User) -> Company:
    return _get_scoped(db, company_id, actor)


def list_companies(db: Session, actor: User, page: int, page_size: int) -> tuple[list[Company], int]:
    if actor.role == Role.SUPER_ADMIN:
        return company_repo.list_paginated(db, page, page_size)
    company = company_repo.get(db, actor.company_id) if actor.company_id else None
    return ([company], 1) if company else ([], 0)


def update_company(db: Session, company_id, data: CompanyUpdate, actor: User) -> Company:
    company = _get_scoped(db, company_id, actor)
    updates = data.model_dump(exclude_unset=True)
    # Only SUPER_ADMIN may change lifecycle status.
    if actor.role != Role.SUPER_ADMIN:
        updates.pop("status", None)
    for key, value in updates.items():
        setattr(company, key, value)
    db.flush()
    audit_repo.create(
        db,
        action=AuditAction.COMPANY_UPDATED,
        user_id=actor.id,
        company_id=company.id,
        entity_type="company",
        entity_id=company.id,
        meta=updates,
    )
    return company


# ---- Locations ----
def list_locations(db: Session, company_id, actor: User):
    _get_scoped(db, company_id, actor)
    return location_repo.list_by_company(db, company_id)


def create_location(db: Session, company_id, data: LocationCreate, actor: User):
    company = _get_scoped(db, company_id, actor)
    return location_repo.create(
        db,
        company_id=company.id,
        name=data.name,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude,
        allowed_radius_meters=data.allowed_radius_meters or settings.DEFAULT_ALLOWED_RADIUS_METERS,
        is_primary=False,
    )


def update_location(db: Session, company_id, loc_id, data: LocationUpdate, actor: User):
    _get_scoped(db, company_id, actor)
    loc = location_repo.get(db, loc_id)
    if not loc or loc.company_id != company_id:
        raise not_found("Location not found.")
    updates = data.model_dump(exclude_unset=True)
    if updates.get("is_primary") is True:
        location_repo.clear_primary(db, company_id)
    for key, value in updates.items():
        setattr(loc, key, value)
    db.flush()
    return loc
