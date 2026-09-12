import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class EmployeeCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)
    phone: str | None = None
    first_name: str
    last_name: str
    employee_code: str = Field(min_length=1, max_length=40)
    department: str | None = None
    designation: str | None = None
    joining_date: date | None = None


class EmployeeUpdate(BaseModel):
    phone: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    department: str | None = None
    designation: str | None = None
    joining_date: date | None = None
    status: str | None = None


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)


class EmployeeOut(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID
    company_id: uuid.UUID
    employee_code: str
    email: str | None = None
    first_name: str
    last_name: str
    phone: str | None = None
    department: str | None = None
    designation: str | None = None
    joining_date: date | None = None
    status: str
    created_at: datetime
