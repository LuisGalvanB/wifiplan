"""Tests for AP catalog and placement endpoints."""
import pytest


def _create_floor(client, auth_headers, org_id):
    """Helper: project → building → floor, return floor_id."""
    proj = client.post(
        f"/api/v1/orgs/{org_id}/projects",
        json={"name": "AP Test Project"},
        headers=auth_headers,
    ).json()
    bld = client.post(
        f"/api/v1/orgs/{org_id}/projects/{proj['id']}/buildings",
        json={"name": "Building A"},
        headers=auth_headers,
    ).json()
    flr = client.post(
        f"/api/v1/orgs/{org_id}/projects/{proj['id']}/buildings/{bld['id']}/floors",
        json={"name": "Ground Floor", "level": 0},
        headers=auth_headers,
    ).json()
    return flr["id"]


# ── Catalog ────────────────────────────────────────────────────────────────────

def test_list_vendors_empty_before_seed(client, demo_user, auth_headers):
    """Vendors list is empty before seeding — catalog is populated by seed script."""
    resp = client.get("/api/v1/catalog/vendors", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_vendors_after_seed(client, demo_user, auth_headers, db):
    """Seed the catalog and verify vendors appear."""
    from app.seeds.ap_catalog import seed_ap_catalog
    seed_ap_catalog(db)

    resp = client.get("/api/v1/catalog/vendors", headers=auth_headers)
    assert resp.status_code == 200
    vendors = resp.json()
    slugs = [v["slug"] for v in vendors]
    assert "cisco" in slugs
    assert "fortinet" in slugs
    assert "ubiquiti" in slugs
    assert len(vendors) == 8


def test_list_models_after_seed(client, demo_user, auth_headers, db):
    """Models can be filtered by vendor."""
    from app.seeds.ap_catalog import seed_ap_catalog
    seed_ap_catalog(db)

    # All models
    all_models = client.get("/api/v1/catalog/models", headers=auth_headers).json()
    assert len(all_models) == 16  # 8 vendors × 2 models each

    # Fortinet models only
    vendors = client.get("/api/v1/catalog/vendors", headers=auth_headers).json()
    fortinet = next(v for v in vendors if v["slug"] == "fortinet")
    fortinet_models = client.get(
        f"/api/v1/catalog/models?vendor_id={fortinet['id']}", headers=auth_headers
    ).json()
    assert len(fortinet_models) == 2
    model_names = [m["model_name"] for m in fortinet_models]
    assert "FortiAP 431F" in model_names


def test_get_model_detail(client, demo_user, auth_headers, db):
    from app.seeds.ap_catalog import seed_ap_catalog
    seed_ap_catalog(db)

    models = client.get("/api/v1/catalog/models", headers=auth_headers).json()
    model_id = models[0]["id"]

    resp = client.get(f"/api/v1/catalog/models/{model_id}", headers=auth_headers)
    assert resp.status_code == 200
    m = resp.json()
    assert "vendor_name" in m
    assert "bands_ghz" in m
    assert isinstance(m["bands_ghz"], list)


# ── AP Placement ──────────────────────────────────────────────────────────────

def test_place_ap_on_floor(client, demo_user, auth_headers, db):
    from app.seeds.ap_catalog import seed_ap_catalog
    seed_ap_catalog(db)

    org_id = str(demo_user["org"].id)
    floor_id = _create_floor(client, auth_headers, org_id)

    models = client.get("/api/v1/catalog/models", headers=auth_headers).json()
    model_id = models[0]["id"]

    resp = client.post(
        f"/api/v1/floors/{floor_id}/aps",
        json={
            "ap_model_id": model_id,
            "x_px": 250.0,
            "y_px": 180.0,
            "tx_power_dbm": 17.0,
            "bands_active": [2.4, 5],
            "label": "AP-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    ap = resp.json()
    assert ap["x_px"] == 250.0
    assert ap["y_px"] == 180.0
    assert ap["label"] == "AP-01"
    assert ap["ap_model_id"] == model_id


def test_list_placed_aps(client, demo_user, auth_headers, db):
    from app.seeds.ap_catalog import seed_ap_catalog
    seed_ap_catalog(db)

    org_id = str(demo_user["org"].id)
    floor_id = _create_floor(client, auth_headers, org_id)
    models = client.get("/api/v1/catalog/models", headers=auth_headers).json()
    model_id = models[0]["id"]

    # Place 3 APs
    for i in range(3):
        client.post(f"/api/v1/floors/{floor_id}/aps", json={
            "ap_model_id": model_id, "x_px": i * 100.0, "y_px": 50.0,
            "label": f"AP-{i+1:02d}",
        }, headers=auth_headers)

    resp = client.get(f"/api/v1/floors/{floor_id}/aps", headers=auth_headers)
    assert resp.status_code == 200
    aps = resp.json()
    assert len(aps) == 3
    # AP model should be included in response
    assert aps[0]["ap_model"] is not None


def test_update_ap_position(client, demo_user, auth_headers, db):
    from app.seeds.ap_catalog import seed_ap_catalog
    seed_ap_catalog(db)

    org_id = str(demo_user["org"].id)
    floor_id = _create_floor(client, auth_headers, org_id)
    model_id = client.get("/api/v1/catalog/models", headers=auth_headers).json()[0]["id"]

    ap = client.post(f"/api/v1/floors/{floor_id}/aps", json={
        "ap_model_id": model_id, "x_px": 100.0, "y_px": 100.0,
    }, headers=auth_headers).json()

    updated = client.patch(
        f"/api/v1/floors/{floor_id}/aps/{ap['id']}",
        json={"x_px": 300.0, "y_px": 200.0, "label": "AP-moved"},
        headers=auth_headers,
    ).json()

    assert updated["x_px"] == 300.0
    assert updated["y_px"] == 200.0
    assert updated["label"] == "AP-moved"


def test_delete_ap(client, demo_user, auth_headers, db):
    from app.seeds.ap_catalog import seed_ap_catalog
    seed_ap_catalog(db)

    org_id = str(demo_user["org"].id)
    floor_id = _create_floor(client, auth_headers, org_id)
    model_id = client.get("/api/v1/catalog/models", headers=auth_headers).json()[0]["id"]

    ap = client.post(f"/api/v1/floors/{floor_id}/aps", json={
        "ap_model_id": model_id, "x_px": 50.0, "y_px": 50.0,
    }, headers=auth_headers).json()

    del_resp = client.delete(
        f"/api/v1/floors/{floor_id}/aps/{ap['id']}", headers=auth_headers
    )
    assert del_resp.status_code == 204

    aps = client.get(f"/api/v1/floors/{floor_id}/aps", headers=auth_headers).json()
    assert len(aps) == 0


def test_place_ap_invalid_model(client, demo_user, auth_headers, db):
    org_id = str(demo_user["org"].id)
    floor_id = _create_floor(client, auth_headers, org_id)

    resp = client.post(f"/api/v1/floors/{floor_id}/aps", json={
        "ap_model_id": "00000000-0000-0000-0000-000000000000",
        "x_px": 100.0, "y_px": 100.0,
    }, headers=auth_headers)
    assert resp.status_code == 404


def test_floor_scale_update(client, demo_user, auth_headers, db):
    """Direct floor PATCH to set scale_px_per_m (used by calibration modal)."""
    org_id = str(demo_user["org"].id)
    floor_id = _create_floor(client, auth_headers, org_id)

    resp = client.patch(
        f"/api/v1/floors/{floor_id}",
        json={"scale_px_per_m": 25.5},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["scale_px_per_m"] == pytest.approx(25.5)


def test_rf_enqueue_failure_marks_job_failed_without_leaking_error(
    client, demo_user, auth_headers, db, monkeypatch
):
    from app.models.jobs import Job, JobStatus, JobType
    from app.workers.tasks import run_rf_simulation

    org_id = str(demo_user["org"].id)
    floor_id = _create_floor(client, auth_headers, org_id)

    def fail_enqueue(*args, **kwargs):
        raise RuntimeError("broker credentials must not reach the client")

    monkeypatch.setattr(run_rf_simulation, "delay", fail_enqueue)
    response = client.post(
        f"/api/v1/floors/{floor_id}/rf/simulate",
        json={"band_ghz": "5", "grid_resolution_px": 10},
        headers=auth_headers,
    )

    assert response.status_code == 503
    assert "broker credentials" not in response.text
    job = (
        db.query(Job)
        .filter(
            Job.organization_id == demo_user["org"].id,
            Job.job_type == JobType.rf_simulation,
        )
        .one()
    )
    assert job.status == JobStatus.failed
    assert job.error_message == "RF simulation could not be queued"


def test_memberships_returns_org(client, demo_user, auth_headers):
    """GET /auth/me/memberships returns the user's organization."""
    resp = client.get("/api/v1/auth/me/memberships", headers=auth_headers)
    assert resp.status_code == 200
    memberships = resp.json()
    assert len(memberships) == 1
    assert memberships[0]["organization_slug"] == demo_user["org"].slug
    assert memberships[0]["role"] == "admin"
