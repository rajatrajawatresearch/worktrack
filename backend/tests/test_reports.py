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

INSIDE = gps(offset_lat(BASE_LAT, 25), BASE_LON, accuracy=12.0)


def _setup_completed_attendance(client, db):
    company, admin, apw = make_company(db, code="RPT", radius=150)
    _emp, user, epw = make_employee(db, company, code="E1")
    etoken = login(client, user.email, epw)
    client.post("/api/v1/attendance/punch-in", json=INSIDE, headers=auth_header(etoken))
    client.post("/api/v1/attendance/punch-out", json=INSIDE, headers=auth_header(etoken))
    return admin, apw


def test_csv_export(client, db_session):
    admin, apw = _setup_completed_attendance(client, db_session)
    atoken = login(client, admin.email, apw)
    r = client.get(
        "/api/v1/reports/attendance?type=daily&format=csv", headers=auth_header(atoken)
    )
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "employee_code" in r.text
    assert "E1" in r.text


def test_report_json_paginated(client, db_session):
    admin, apw = _setup_completed_attendance(client, db_session)
    atoken = login(client, admin.email, apw)
    r = client.get(
        "/api/v1/reports/attendance?type=hours&format=json", headers=auth_header(atoken)
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert "pagination" in body


def test_dashboard_summary(client, db_session):
    admin, apw = _setup_completed_attendance(client, db_session)
    atoken = login(client, admin.email, apw)
    r = client.get("/api/v1/dashboard/summary", headers=auth_header(atoken))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_employees"] == 1
    assert data["completed"] == 1
    assert data["present"] == 1


def test_invalid_report_type(client, db_session):
    admin, apw = _setup_completed_attendance(client, db_session)
    atoken = login(client, admin.email, apw)
    r = client.get(
        "/api/v1/reports/attendance?type=bogus", headers=auth_header(atoken)
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
