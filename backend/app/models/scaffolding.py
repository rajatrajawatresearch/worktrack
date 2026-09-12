"""Future-module scaffolding tables.

These tables exist in the schema/migration so future modules (shift
management, holiday calendars, leave management) can be built without a
disruptive migration. V1 does NOT implement business logic for them.
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import GUID
from app.models.base import TimestampMixin, UUIDMixin


class Shift(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "shifts"

    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    start_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "09:00"
    end_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "18:00"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")


class Holiday(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "holidays"

    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    holiday_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)


class LeaveRequest(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "leave_requests"

    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    leave_type: Mapped[str] = mapped_column(String(30), nullable=False, default="CASUAL")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
