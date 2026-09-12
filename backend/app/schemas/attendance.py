import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.common import LocationInfo, ORMModel


class BreakOut(ORMModel):
    id: uuid.UUID
    break_type: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_minutes: int | None = None


class AttendanceOut(ORMModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    company_id: uuid.UUID
    attendance_date: date
    punch_in_at: datetime | None = None
    punch_in_latitude: float | None = None
    punch_in_longitude: float | None = None
    punch_in_accuracy: float | None = None
    punch_in_distance_meters: float | None = None
    punch_out_at: datetime | None = None
    punch_out_latitude: float | None = None
    punch_out_longitude: float | None = None
    punch_out_accuracy: float | None = None
    punch_out_distance_meters: float | None = None
    total_work_minutes: int | None = None
    status: str
    breaks: list[BreakOut] = []


class TodayState(BaseModel):
    date: date
    status: str
    on_break: bool
    current_work_minutes: int
    server_time: datetime
    attendance: AttendanceOut | None = None


class PunchResult(BaseModel):
    attendance: AttendanceOut
    location: LocationInfo
    current_work_minutes: int


# Admin list row (flattened with employee identity for tables/CSV)
class AttendanceAdminRow(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    employee_code: str
    employee_name: str
    department: str | None = None
    attendance_date: date
    punch_in_at: datetime | None = None
    punch_out_at: datetime | None = None
    break_minutes: int
    total_work_minutes: int | None = None
    status: str
