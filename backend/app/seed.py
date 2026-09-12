"""Seed initial data.

Usage:
    python -m app.seed              # create super admin only
    python -m app.seed --create-all # also create tables first (dev/sqlite)
    python -m app.seed --demo       # also create a demo company + admin + employee

Credentials come from environment (see .env.example). Never commit real ones.
"""

import sys
from datetime import date

from app.core import security
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.enums import Role
from app.repositories import company_repo, employee_repo, location_repo, user_repo

DEMO_COMPANY_CODE = "DEMO"
DEMO_ADMIN_EMAIL = "admin@demo.local"
DEMO_ADMIN_PASSWORD = "Admin123!"
DEMO_EMPLOYEE_EMAIL = "john@demo.local"
DEMO_EMPLOYEE_PASSWORD = "Employee123!"


def _seed_super_admin(db) -> None:
    if user_repo.get_by_email(db, settings.SUPERADMIN_EMAIL):
        print(f"[seed] super admin already exists: {settings.SUPERADMIN_EMAIL}")
        return
    user_repo.create(
        db,
        email=settings.SUPERADMIN_EMAIL,
        password_hash=security.hash_password(settings.SUPERADMIN_PASSWORD),
        role=Role.SUPER_ADMIN,
    )
    print(f"[seed] created super admin: {settings.SUPERADMIN_EMAIL}")


def _seed_demo(db) -> None:
    if company_repo.get_by_code(db, DEMO_COMPANY_CODE):
        print("[seed] demo company already exists.")
        return
    company = company_repo.create(
        db,
        name="Demo Company",
        code=DEMO_COMPANY_CODE,
        timezone=settings.DEFAULT_TIMEZONE,
        work_start_time="09:00",
        work_end_time="18:00",
    )
    location_repo.create(
        db,
        company_id=company.id,
        name="Head Office",
        address="MG Road, Bengaluru",
        latitude=12.9716,
        longitude=77.5946,
        allowed_radius_meters=settings.DEFAULT_ALLOWED_RADIUS_METERS,
        is_primary=True,
    )
    user_repo.create(
        db,
        email=DEMO_ADMIN_EMAIL,
        password_hash=security.hash_password(DEMO_ADMIN_PASSWORD),
        role=Role.COMPANY_ADMIN,
        company_id=company.id,
    )
    emp_user = user_repo.create(
        db,
        email=DEMO_EMPLOYEE_EMAIL,
        password_hash=security.hash_password(DEMO_EMPLOYEE_PASSWORD),
        role=Role.EMPLOYEE,
        company_id=company.id,
    )
    employee_repo.create(
        db,
        user_id=emp_user.id,
        company_id=company.id,
        employee_code="EMP001",
        first_name="John",
        last_name="Doe",
        department="Engineering",
        designation="Software Engineer",
        joining_date=date(2026, 1, 1),
    )
    print("[seed] created demo company, admin and employee.")
    print(f"       company admin: {DEMO_ADMIN_EMAIL} / {DEMO_ADMIN_PASSWORD}")
    print(f"       employee:      {DEMO_EMPLOYEE_EMAIL} / {DEMO_EMPLOYEE_PASSWORD}")


def seed(create_all: bool = False, demo: bool = False) -> None:
    if create_all:
        Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _seed_super_admin(db)
        if demo:
            _seed_demo(db)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed(create_all="--create-all" in sys.argv, demo="--demo" in sys.argv)
