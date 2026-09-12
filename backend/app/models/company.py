from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.database import Base
from app.core.enums import CompanyStatus
from app.models.base import TimestampMixin, UUIDMixin


class Company(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=CompanyStatus.ACTIVE)
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default=settings.DEFAULT_TIMEZONE
    )

    # Attendance policy (per-company overrides of global defaults)
    max_accuracy_meters: Mapped[float] = mapped_column(
        Float, nullable=False, default=settings.MAX_ACCEPTABLE_ACCURACY_METERS
    )
    work_start_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "09:00"
    work_end_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "18:00"
    late_grace_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    standard_work_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=480)

    locations: Mapped[list["CompanyLocation"]] = relationship(  # noqa: F821
        "CompanyLocation", back_populates="company", cascade="all, delete-orphan"
    )
