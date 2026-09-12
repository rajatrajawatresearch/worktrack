import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


# ---- Locations ----
class LocationCreate(BaseModel):
    name: str
    address: str | None = None
    latitude: float
    longitude: float
    allowed_radius_meters: int | None = Field(default=None, ge=10, le=5000)


class LocationUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    allowed_radius_meters: int | None = Field(default=None, ge=10, le=5000)
    is_primary: bool | None = None
    status: str | None = None


class LocationOut(ORMModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    address: str | None = None
    latitude: float
    longitude: float
    allowed_radius_meters: int
    is_primary: bool
    status: str


# ---- Companies ----
class CompanyCreate(BaseModel):
    name: str
    code: str = Field(min_length=2, max_length=30)
    timezone: str | None = None
    admin_email: str
    admin_password: str = Field(min_length=8)
    location: LocationCreate


class CompanyUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    timezone: str | None = None
    max_accuracy_meters: float | None = Field(default=None, gt=0, le=5000)
    work_start_time: str | None = None
    work_end_time: str | None = None
    late_grace_minutes: int | None = Field(default=None, ge=0, le=240)
    standard_work_minutes: int | None = Field(default=None, ge=0, le=1440)


class CompanyOut(ORMModel):
    id: uuid.UUID
    name: str
    code: str
    status: str
    timezone: str
    max_accuracy_meters: float
    work_start_time: str | None = None
    work_end_time: str | None = None
    late_grace_minutes: int
    standard_work_minutes: int
    created_at: datetime
