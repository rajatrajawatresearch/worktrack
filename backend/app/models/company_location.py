import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.database import Base
from app.core.enums import CompanyStatus
from app.core.types import GUID
from app.models.base import TimestampMixin, UUIDMixin


class CompanyLocation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "company_locations"

    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str | None] = mapped_column(String(400), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    allowed_radius_meters: Mapped[int] = mapped_column(
        Integer, nullable=False, default=settings.DEFAULT_ALLOWED_RADIUS_METERS
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=CompanyStatus.ACTIVE)

    company: Mapped["Company"] = relationship("Company", back_populates="locations")  # noqa: F821
