from tests.helpers import auth_header, login, make_super_admin


def test_login_success_and_me(client, db_session):
    user, pw = make_super_admin(db_session)
    token = login(client, user.email, pw)
    r = client.get("/api/v1/me", headers=auth_header(token))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["user"]["email"] == user.email
    assert data["user"]["role"] == "SUPER_ADMIN"
    assert data["company"] is None


def test_login_wrong_password(client, db_session):
    user, _pw = make_super_admin(db_session)
    r = client.post("/api/v1/auth/login", json={"email": user.email, "password": "wrong"})
    assert r.status_code == 401
    body = r.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_CREDENTIALS"


def test_refresh_rotates_and_revokes_old(client, db_session):
    user, pw = make_super_admin(db_session)
    tokens = client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": pw}
    ).json()["data"]
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r2.status_code == 200
    assert r2.json()["data"]["access_token"]
    # Old refresh token must now be rejected (rotation).
    r3 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r3.status_code == 401
    assert r3.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"


def test_logout_revokes_refresh(client, db_session):
    user, pw = make_super_admin(db_session)
    tokens = client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": pw}
    ).json()["data"]
    r = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=auth_header(tokens["access_token"]),
    )
    assert r.status_code == 200
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r2.status_code == 401


def test_protected_requires_token(client):
    r = client.get("/api/v1/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_login_rate_limited(client, db_session):
    user, _pw = make_super_admin(db_session)
    for _ in range(5):
        client.post("/api/v1/auth/login", json={"email": user.email, "password": "bad"})
    r = client.post("/api/v1/auth/login", json={"email": user.email, "password": "bad"})
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "RATE_LIMITED"
