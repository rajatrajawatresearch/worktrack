import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import AttendanceStatus
from app.core.types import GUID
from app.models.base import TimestampMixin, UUIDMixin


class Attendance(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "attendance"
    __table_args__ = (
        # One normal attendance record per employee per date.
        UniqueConstraint("employee_id", "attendance_date", name="uq_attendance_employee_date"),
        Index("ix_attendance_company_date", "company_id", "attendance_date"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Punch in
    punch_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    punch_in_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    punch_in_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    punch_in_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    punch_in_distance_meters: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Punch out
    punch_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    punch_out_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    punch_out_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    punch_out_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    punch_out_distance_meters: Mapped[float | None] = mapped_column(Float, nullable=True)

    total_work_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AttendanceStatus.IN_PROGRESS
    )

    breaks: Mapped[list["AttendanceBreak"]] = relationship(  # noqa: F821
        "AttendanceBreak",
        back_populates="attendance",
        cascade="all, delete-orphan",
        order_by="AttendanceBreak.started_at",
    )
    employee: Mapped["Employee"] = relationship("Employee")  # noqa: F821
