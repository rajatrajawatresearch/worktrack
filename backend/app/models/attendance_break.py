import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import BreakType
from app.core.types import GUID
from app.models.base import UUIDMixin, _utcnow


class AttendanceBreak(UUIDMixin, Base):
    __tablename__ = "attendance_breaks"

    attendance_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("attendance.id", ondelete="CASCADE"), nullable=False, index=True
    )
    break_type: Mapped[str] = mapped_column(String(20), nullable=False, default=BreakType.REGULAR)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    attendance: Mapped["Attendance"] = relationship(  # noqa: F821
        "Attendance", back_populates="breaks"
    )
