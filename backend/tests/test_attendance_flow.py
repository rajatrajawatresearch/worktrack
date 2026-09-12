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

INSIDE = gps(offset_lat(BASE_LAT, 30), BASE_LON, accuracy=12.0)


def _employee_token(client, db):
    company, _admin, _apw = make_company(db, code="FLOW", radius=150)
    _emp, user, epw = make_employee(db, company, code="E1")
    return login(client, user.email, epw)


def _post(client, token, path, payload=INSIDE):
    return client.post(f"/api/v1/attendance/{path}", json=payload, headers=auth_header(token))


def test_full_attendance_flow(client, db_session):
    token = _employee_token(client, db_session)

    r = client.get("/api/v1/attendance/today", headers=auth_header(token))
    assert r.json()["data"]["status"] == "NOT_STARTED"

    assert _post(client, token, "punch-in").status_code == 200
    r = _post(client, token, "break/start")
    assert r.status_code == 200
    assert r.json()["data"]["attendance"]["status"] == "ON_BREAK"
    assert r.json()["data"]["on_break"] is True

    r = _post(client, token, "break/end")
    assert r.status_code == 200
    assert r.json()["data"]["attendance"]["status"] == "IN_PROGRESS"
    assert r.json()["data"]["on_break"] is False

    r = _post(client, token, "punch-out")
    assert r.status_code == 200
    att = r.json()["data"]["attendance"]
    assert att["status"] == "COMPLETED"
    assert att["total_work_minutes"] is not None
    assert len(att["breaks"]) == 1


def test_duplicate_punch_in_rejected(client, db_session):
    token = _employee_token(client, db_session)
    assert _post(client, token, "punch-in").status_code == 200
    r = _post(client, token, "punch-in")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ALREADY_PUNCHED_IN"


def test_break_end_without_active_break(client, db_session):
    token = _employee_token(client, db_session)
    _post(client, token, "punch-in")
    r = _post(client, token, "break/end")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "NOT_ON_BREAK"


def test_double_break_start_rejected(client, db_session):
    token = _employee_token(client, db_session)
    _post(client, token, "punch-in")
    _post(client, token, "break/start")
    r = _post(client, token, "break/start")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ALREADY_ON_BREAK"


def test_punch_out_without_punch_in(client, db_session):
    token = _employee_token(client, db_session)
    r = _post(client, token, "punch-out")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "NOT_PUNCHED_IN"


def test_punch_out_while_on_break_blocked(client, db_session):
    token = _employee_token(client, db_session)
    _post(client, token, "punch-in")
    _post(client, token, "break/start")
    r = _post(client, token, "punch-out")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ON_BREAK_CANNOT_PUNCH_OUT"
