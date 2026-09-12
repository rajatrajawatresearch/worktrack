import uuid
from datetime import datetime

from app.schemas.common import ORMModel


class UserOut(ORMModel):
    id: uuid.UUID
    email: str
    phone: str | None = None
    role: str
    status: str
    company_id: uuid.UUID | None = None
    last_login_at: datetime | None = None
