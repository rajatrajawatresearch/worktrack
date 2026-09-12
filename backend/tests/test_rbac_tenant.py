"""RBAC + multi-tenant isolation. Company A must NEVER reach Company B data."""

from tests.helpers import auth_header, login, make_company, make_employee, make_super_admin


def test_company_admin_cannot_read_other_company(client, db_session):
    make_super_admin(db_session)
    _company_a, admin_a, apw = make_company(db_session, code="AAA")
    company_b, _admin_b, _bpw = make_company(db_session, code="BBB")
    token_a = login(client, admin_a.email, apw)

    r = client.get(f"/api/v1/companies/{company_b.id}", headers=auth_header(token_a))
    assert r.status_code == 403
    assert r.json()["success"] is False


def test_company_admin_employee_list_is_scoped(client, db_session):
    make_super_admin(db_session)
    company_a, admin_a, apw = make_company(db_session, code="AAA")
    company_b, _admin_b, _bpw = make_company(db_session, code="BBB")
    make_employee(db_session, company_a, code="A1")
    make_employee(db_session, company_b, code="B1")
    token_a = login(client, admin_a.email, apw)

    r = client.get("/api/v1/employees", headers=auth_header(token_a))
    assert r.status_code == 200
    codes = [e["employee_code"] for e in r.json()["data"]]
    assert "A1" in codes
    assert "B1" not in codes


def test_company_admin_cannot_read_other_companys_employee(client, db_session):
    make_super_admin(db_session)
    _company_a, admin_a, apw = make_company(db_session, code="AAA")
    company_b, _admin_b, _bpw = make_company(db_session, code="BBB")
    emp_b, _u, _p = make_employee(db_session, company_b, code="B1")
    token_a = login(client, admin_a.email, apw)

    r = client.get(f"/api/v1/employees/{emp_b.id}", headers=auth_header(token_a))
    assert r.status_code == 404


def test_employee_cannot_access_admin_endpoints(client, db_session):
    company, _admin, _apw = make_company(db_session, code="AAA")
    _emp, user, epw = make_employee(db_session, company, code="A1")
    token = login(client, user.email, epw)

    r = client.get("/api/v1/employees", headers=auth_header(token))
    assert r.status_code == 403


def test_employee_cannot_create_company(client, db_session):
    company, _admin, _apw = make_company(db_session, code="AAA")
    _emp, user, epw = make_employee(db_session, company, code="A1")
    token = login(client, user.email, epw)
    r = client.post(
        "/api/v1/companies",
        json={
            "name": "X",
            "code": "XXX",
            "admin_email": "x@x.local",
            "admin_password": "Passw0rd!",
            "location": {"name": "HQ", "latitude": 1.0, "longitude": 1.0},
        },
        headers=auth_header(token),
    )
    assert r.status_code == 403


def test_super_admin_can_access_any_company(client, db_session):
    superu, spw = make_super_admin(db_session)
    company_a, _admin_a, _apw = make_company(db_session, code="AAA")
    token = login(client, superu.email, spw)
    r = client.get(f"/api/v1/companies/{company_a.id}", headers=auth_header(token))
    assert r.status_code == 200
    assert r.json()["data"]["code"] == "AAA"


def test_super_admin_creates_company_and_admin_can_login(client, db_session):
    superu, spw = make_super_admin(db_session)
    token = login(client, superu.email, spw)
    r = client.post(
        "/api/v1/companies",
        json={
            "name": "New Co",
            "code": "NEWCO",
            "admin_email": "boss@newco.local",
            "admin_password": "Passw0rd!",
            "location": {
                "name": "HQ",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "allowed_radius_meters": 150,
            },
        },
        headers=auth_header(token),
    )
    assert r.status_code == 201, r.text
    # The new company admin can authenticate.
    admin_token = login(client, "boss@newco.local", "Passw0rd!")
    assert admin_token
