def test_create_project(client, demo_user, auth_headers):
    org_id = str(demo_user["org"].id)
    resp = client.post(
        f"/api/v1/orgs/{org_id}/projects",
        json={"name": "Test Site", "description": "A test site"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Site"
    assert data["organization_id"] == org_id


def test_list_projects_empty(client, demo_user, auth_headers):
    org_id = str(demo_user["org"].id)
    resp = client.get(f"/api/v1/orgs/{org_id}/projects", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_projects_after_create(client, demo_user, auth_headers):
    org_id = str(demo_user["org"].id)
    client.post(f"/api/v1/orgs/{org_id}/projects", json={"name": "Site A"}, headers=auth_headers)
    client.post(f"/api/v1/orgs/{org_id}/projects", json={"name": "Site B"}, headers=auth_headers)
    resp = client.get(f"/api/v1/orgs/{org_id}/projects", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_project_not_found(client, demo_user, auth_headers):
    org_id = str(demo_user["org"].id)
    resp = client.get(
        f"/api/v1/orgs/{org_id}/projects/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_create_building_and_floor(client, demo_user, auth_headers):
    org_id = str(demo_user["org"].id)

    # Create project
    proj = client.post(
        f"/api/v1/orgs/{org_id}/projects",
        json={"name": "RF Project"},
        headers=auth_headers,
    ).json()

    # Create building
    bld = client.post(
        f"/api/v1/orgs/{org_id}/projects/{proj['id']}/buildings",
        json={"name": "Main Building"},
        headers=auth_headers,
    ).json()
    assert bld["name"] == "Main Building"

    # Create floor
    flr = client.post(
        f"/api/v1/orgs/{org_id}/projects/{proj['id']}/buildings/{bld['id']}/floors",
        json={"name": "Ground Floor", "level": 0},
        headers=auth_headers,
    ).json()
    assert flr["name"] == "Ground Floor"
    assert flr["level"] == 0


def test_unauthorized_project_access(client, db):
    """Another user can't access org they don't belong to."""
    # Register second user with different org
    client.post("/api/v1/auth/register", json={
        "email": "other@example.com",
        "password": "OtherPass1!",
        "org_name": "Other Corp",
        "org_slug": "other-corp",
    })
    login = client.post("/api/v1/auth/login", json={
        "email": "other@example.com",
        "password": "OtherPass1!",
    })
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Register first user to get an org_id
    client.post("/api/v1/auth/register", json={
        "email": "first@example.com",
        "password": "FirstPass1!",
        "org_name": "First Corp",
        "org_slug": "first-corp",
    })
    login1 = client.post("/api/v1/auth/login", json={
        "email": "first@example.com", "password": "FirstPass1!",
    })
    first_headers = {"Authorization": f"Bearer {login1.json()['access_token']}"}

    from app.models.tenant import Organization
    first_org = db.query(Organization).filter_by(slug="first-corp").one()
    # Try accessing first org's projects with other user's token
    # We expect 403 from membership check
    assert client.get("/api/v1/auth/me", headers=first_headers).status_code == 200
    fake_resp = client.get(
        f"/api/v1/orgs/{first_org.id}/projects",
        headers=other_headers,
    )
    assert fake_resp.status_code in (403, 404)
