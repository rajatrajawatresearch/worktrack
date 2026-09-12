"""Import all models so ``Base.metadata`` is fully populated (Alembic + tests)."""

from app.models.attendance import Attendance
from app.models.attendance_break import AttendanceBreak
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.company_location import CompanyLocation
from app.models.employee import Employee
from app.models.refresh_token import RefreshToken
from app.models.scaffolding import Holiday, LeaveRequest, Shift
from app.models.user import User

__all__ = [
    "Attendance",
    "AttendanceBreak",
    "AuditLog",
    "Company",
    "CompanyLocation",
    "Employee",
    "Holiday",
    "LeaveRequest",
    "RefreshToken",
    "Shift",
    "User",
]
