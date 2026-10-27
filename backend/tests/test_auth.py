def test_register_creates_user_and_org(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "SecurePass1!",
        "full_name": "New User",
        "org_name": "New Corp",
        "org_slug": "new-corp",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_register_duplicate_email_fails(client, demo_user):
    resp = client.post("/api/v1/auth/register", json={
        "email": demo_user["user"].email,
        "password": "SecurePass1!",
        "org_name": "Other",
        "org_slug": "other-slug",
    })
    assert resp.status_code == 400


def test_register_duplicate_slug_fails(client, demo_user):
    resp = client.post("/api/v1/auth/register", json={
        "email": "other@example.com",
        "password": "SecurePass1!",
        "org_name": "Other",
        "org_slug": demo_user["org"].slug,
    })
    assert resp.status_code == 400


def test_login_success(client, demo_user):
    resp = client.post("/api/v1/auth/login", json={
        "email": demo_user["user"].email,
        "password": "TestPass1!",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client, demo_user):
    resp = client.post("/api/v1/auth/login", json={
        "email": demo_user["user"].email,
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_me_returns_user(client, demo_user, auth_headers):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == demo_user["user"].email


def test_me_without_token_fails(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 403  # HTTPBearer returns 403 when no header


def test_refresh_token(client, demo_user):
    login = client.post("/api/v1/auth/login", json={
        "email": demo_user["user"].email,
        "password": "TestPass1!",
    })
    refresh_token = login.json()["refresh_token"]
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
