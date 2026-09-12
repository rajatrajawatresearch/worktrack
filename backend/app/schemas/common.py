from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class LocationPayload(BaseModel):
    """GPS payload sent by clients for attendance actions.

    Coordinate ranges + accuracy policy are validated in the service layer so
    we can return precise error codes (INVALID_COORDINATES / GPS_ACCURACY_TOO_LOW).
    """

    latitude: float
    longitude: float
    accuracy: float
    client_timestamp: datetime | None = None


class LocationInfo(BaseModel):
    distance_meters: float
    allowed_radius_meters: int
    accuracy: float
    within_radius: bool


class PageParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
