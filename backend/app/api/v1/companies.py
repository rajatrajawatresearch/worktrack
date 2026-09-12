import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import Pagination, require_admin, require_super_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.company import (
    CompanyCreate,
    CompanyOut,
    CompanyUpdate,
    LocationCreate,
    LocationOut,
    LocationUpdate,
)
from app.services import company_service
from app.utils.responses import paginated, success

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("")
def list_companies(
    pg: Pagination, user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    page, page_size = pg
    rows, total = company_service.list_companies(db, user, page, page_size)
    return paginated(
        [CompanyOut.model_validate(c) for c in rows], page=page, page_size=page_size, total=total
    )


@router.post("", status_code=201)
def create_company(
    payload: CompanyCreate,
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    company = company_service.create_company(db, payload, user)
    db.commit()
    return success(CompanyOut.model_validate(company))


@router.get("/{company_id}")
def get_company(
    company_id: uuid.UUID, user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    company = company_service.get_company(db, company_id, user)
    return success(CompanyOut.model_validate(company))


@router.patch("/{company_id}")
def update_company(
    company_id: uuid.UUID,
    payload: CompanyUpdate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    company = company_service.update_company(db, company_id, payload, user)
    db.commit()
    return success(CompanyOut.model_validate(company))


@router.get("/{company_id}/locations")
def list_locations(
    company_id: uuid.UUID, user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    locations = company_service.list_locations(db, company_id, user)
    return success([LocationOut.model_validate(loc) for loc in locations])


@router.post("/{company_id}/locations", status_code=201)
def create_location(
    company_id: uuid.UUID,
    payload: LocationCreate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    loc = company_service.create_location(db, company_id, payload, user)
    db.commit()
    return success(LocationOut.model_validate(loc))


@router.patch("/{company_id}/locations/{loc_id}")
def update_location(
    company_id: uuid.UUID,
    loc_id: uuid.UUID,
    payload: LocationUpdate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    loc = company_service.update_location(db, company_id, loc_id, payload, user)
    db.commit()
    return success(LocationOut.model_validate(loc))
