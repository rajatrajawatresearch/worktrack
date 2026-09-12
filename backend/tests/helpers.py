"""Test data factories + auth helpers."""

from app.core import security
from app.core.enums import Role
from app.repositories import company_repo, employee_repo, location_repo, user_repo

BASE_LAT = 12.9716
BASE_LON = 77.5946
METERS_PER_DEG_LAT = 111_320.0


def offset_lat(base_lat: float, meters: float) -> float:
    """Return a latitude offset north of base_lat by ~`meters`."""
    return base_lat + meters / METERS_PER_DEG_LAT


def make_super_admin(db, email="super@wt.local", password="Passw0rd!"):
    user = user_repo.create(
        db,
        email=email,
        password_hash=security.hash_password(password),
        role=Role.SUPER_ADMIN,
    )
    db.commit()
    return user, password


def make_company(
    db,
    *,
    code="ACME",
    name="Acme Inc",
    lat=BASE_LAT,
    lon=BASE_LON,
    radius=150,
    max_accuracy=100.0,
    admin_password="Passw0rd!",
):
    company = company_repo.create(
        db, name=name, code=code, timezone="Asia/Kolkata", max_accuracy_meters=max_accuracy
    )
    location_repo.create(
        db,
        company_id=company.id,
        name="HQ",
        latitude=lat,
        longitude=lon,
        allowed_radius_meters=radius,
        is_primary=True,
    )
    admin = user_repo.create(
        db,
        email=f"admin@{code.lower()}.local",
        password_hash=security.hash_password(admin_password),
        role=Role.COMPANY_ADMIN,
        company_id=company.id,
    )
    db.commit()
    return company, admin, admin_password


def make_employee(db, company, *, code="E1", email=None, password="Passw0rd!"):
    user = user_repo.create(
        db,
        email=email or f"{code.lower()}@{company.code.lower()}.local",
        password_hash=security.hash_password(password),
        role=Role.EMPLOYEE,
        company_id=company.id,
    )
    emp = employee_repo.create(
        db,
        user_id=user.id,
        company_id=company.id,
        employee_code=code,
        first_name="Test",
        last_name="User",
    )
    db.commit()
    return emp, user, password


def login(client, email, password):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def gps(lat, lon, accuracy=15.0):
    return {"latitude": lat, "longitude": lon, "accuracy": accuracy}
