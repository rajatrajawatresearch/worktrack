import pytest

from app.services import geo
from tests.helpers import (
    BASE_LAT,
    BASE_LON,
    auth_header,
    gps,
    login,
    make_company,
    make_employee,
    offset_lat,
)


def test_haversine_zero_distance():
    assert geo.haversine_meters(BASE_LAT, BASE_LON, BASE_LAT, BASE_LON) == pytest.approx(0, abs=1e-6)


@pytest.mark.parametrize(
    "meters,radius,expected_within",
    [(50, 150, True), (149, 150, True), (151, 150, False), (420, 150, False)],
)
def test_check_location_radius(meters, radius, expected_within):
    check = geo.check_location(
        offset_lat(BASE_LAT, meters), BASE_LON, 10.0, BASE_LAT, BASE_LON, radius, 100.0
    )
    assert check.within_radius is expected_within


def test_coordinates_valid():
    assert geo.coordinates_valid(12.9, 77.5) is True
    assert geo.coordinates_valid(200.0, 77.5) is False
    assert geo.coordinates_valid(12.9, -190.0) is False


def _employee_token(client, db):
    company, _admin, _apw = make_company(db, code="GPS", radius=150, max_accuracy=100.0)
    _emp, user, epw = make_employee(db, company, code="E1")
    return login(client, user.email, epw)


def test_punch_in_inside_radius(client, db_session):
    token = _employee_token(client, db_session)
    r = client.post(
        "/api/v1/attendance/punch-in",
        json=gps(offset_lat(BASE_LAT, 50), BASE_LON, accuracy=15.0),
        headers=auth_header(token),
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["attendance"]["status"] == "IN_PROGRESS"
    assert data["location"]["within_radius"] is True


def test_punch_in_outside_radius(client, db_session):
    token = _employee_token(client, db_session)
    r = client.post(
        "/api/v1/attendance/punch-in",
        json=gps(offset_lat(BASE_LAT, 420), BASE_LON, accuracy=15.0),
        headers=auth_header(token),
    )
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "OUTSIDE_ATTENDANCE_RADIUS"
    assert body["error"]["details"]["allowed_radius_meters"] == 150
    assert body["error"]["details"]["distance_meters"] > 150


def test_punch_in_poor_accuracy(client, db_session):
    token = _employee_token(client, db_session)
    r = client.post(
        "/api/v1/attendance/punch-in",
        json=gps(offset_lat(BASE_LAT, 20), BASE_LON, accuracy=250.0),
        headers=auth_header(token),
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "GPS_ACCURACY_TOO_LOW"


def test_punch_in_missing_gps(client, db_session):
    token = _employee_token(client, db_session)
    r = client.post(
        "/api/v1/attendance/punch-in",
        json={"longitude": BASE_LON, "accuracy": 15.0},
        headers=auth_header(token),
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_punch_in_invalid_coordinates(client, db_session):
    token = _employee_token(client, db_session)
    r = client.post(
        "/api/v1/attendance/punch-in",
        json=gps(200.0, 77.0, accuracy=15.0),
        headers=auth_header(token),
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_COORDINATES"
