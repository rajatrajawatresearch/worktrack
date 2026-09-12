from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_super_admin
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.repositories import attendance_repo, company_repo, employee_repo
from app.utils.responses import success

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/stats")
def stats(_: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    today = datetime.now(ZoneInfo(settings.DEFAULT_TIMEZONE)).date()
    users = db.scalar(select(func.count()).select_from(User)) or 0
    return success(
        {
            "companies": company_repo.count(db),
            "users": users,
            "employees": employee_repo.count_all(db),
            "attendance_today": attendance_repo.count_on_date(db, None, today),
        }
    )
