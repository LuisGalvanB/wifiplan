"""Tests for wall/geometry CRUD endpoints."""


def _setup_floor(client, auth_headers, org_id):
    proj = client.post(
        f"/api/v1/orgs/{org_id}/projects",
        json={"name": "Geo Test Project"},
        headers=auth_headers,
    ).json()
    bld = client.post(
        f"/api/v1/orgs/{org_id}/projects/{proj['id']}/buildings",
        json={"name": "Building A"},
        headers=auth_headers,
    ).json()
    flr = client.post(
        f"/api/v1/orgs/{org_id}/projects/{proj['id']}/buildings/{bld['id']}/floors",
        json={"name": "Floor 1", "level": 0},
        headers=auth_headers,
    ).json()
    return flr["id"]


def test_create_and_list_walls(client, demo_user, auth_headers):
    org_id = str(demo_user["org"].id)
    floor_id = _setup_floor(client, auth_headers, org_id)

    wall_data = {
        "geometry": {"start": {"x": 0, "y": 0}, "end": {"x": 100, "y": 0}},
        "material": "drywall",
        "wall_type": "interior",
    }
    resp = client.post(
        f"/api/v1/floors/{floor_id}/geometry/walls",
        json=wall_data,
        headers=auth_headers,
    )
    assert resp.status_code == 201
    wall = resp.json()
    assert wall["material"] == "drywall"
    assert wall["geometry"]["start"]["x"] == 0

    # List
    list_resp = client.get(f"/api/v1/floors/{floor_id}/geometry/walls", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_update_wall_material(client, demo_user, auth_headers):
    org_id = str(demo_user["org"].id)
    floor_id = _setup_floor(client, auth_headers, org_id)

    wall = client.post(
        f"/api/v1/floors/{floor_id}/geometry/walls",
        json={"geometry": {"start": {"x": 0, "y": 0}, "end": {"x": 50, "y": 0}}, "material": "unknown"},
        headers=auth_headers,
    ).json()

    updated = client.patch(
        f"/api/v1/floors/{floor_id}/geometry/walls/{wall['id']}",
        json={"material": "concrete"},
        headers=auth_headers,
    ).json()
    assert updated["material"] == "concrete"


def test_delete_wall(client, demo_user, auth_headers):
    org_id = str(demo_user["org"].id)
    floor_id = _setup_floor(client, auth_headers, org_id)

    wall = client.post(
        f"/api/v1/floors/{floor_id}/geometry/walls",
        json={"geometry": {"start": {"x": 0, "y": 0}, "end": {"x": 50, "y": 0}}},
        headers=auth_headers,
    ).json()

    del_resp = client.delete(
        f"/api/v1/floors/{floor_id}/geometry/walls/{wall['id']}",
        headers=auth_headers,
    )
    assert del_resp.status_code == 204

    list_resp = client.get(f"/api/v1/floors/{floor_id}/geometry/walls", headers=auth_headers)
    assert len(list_resp.json()) == 0


def test_bulk_create_walls(client, demo_user, auth_headers):
    org_id = str(demo_user["org"].id)
    floor_id = _setup_floor(client, auth_headers, org_id)

    walls = {"walls": [
        {"geometry": {"start": {"x": 0, "y": 0}, "end": {"x": 100, "y": 0}}},
        {"geometry": {"start": {"x": 100, "y": 0}, "end": {"x": 100, "y": 100}}},
        {"geometry": {"start": {"x": 100, "y": 100}, "end": {"x": 0, "y": 100}}},
        {"geometry": {"start": {"x": 0, "y": 100}, "end": {"x": 0, "y": 0}}},
    ]}
    resp = client.post(
        f"/api/v1/floors/{floor_id}/geometry/walls/bulk",
        json=walls,
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["created"] == 4


def test_get_floor_geometry_snapshot(client, demo_user, auth_headers):
    org_id = str(demo_user["org"].id)
    floor_id = _setup_floor(client, auth_headers, org_id)

    # Add a wall and scope zone
    client.post(
        f"/api/v1/floors/{floor_id}/geometry/walls",
        json={"geometry": {"start": {"x": 0, "y": 0}, "end": {"x": 100, "y": 0}}},
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/floors/{floor_id}/geometry/scope-zones",
        json={"geometry": {"points": [{"x": 0, "y": 0}, {"x": 200, "y": 0}, {"x": 200, "y": 200}, {"x": 0, "y": 200}]}},
        headers=auth_headers,
    )

    resp = client.get(f"/api/v1/floors/{floor_id}/geometry", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["walls"]) == 1
    assert len(data["scope_zones"]) == 1
    assert "openings" in data
    assert "obstacles" in data
