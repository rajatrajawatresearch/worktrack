from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.core.database import get_db
from app.schemas.company import CompanyOut
from app.schemas.employee import EmployeeOut
from app.schemas.user import UserOut
from app.services import auth_service
from app.utils.responses import success

router = APIRouter(tags=["me"])


@router.get("/me")
def me(user: CurrentUser, db: Session = Depends(get_db)):
    u, employee, company = auth_service.build_me(db, user)
    return success(
        {
            "user": UserOut.model_validate(u),
            "employee": EmployeeOut.model_validate(employee) if employee else None,
            "company": CompanyOut.model_validate(company) if company else None,
        }
    )
