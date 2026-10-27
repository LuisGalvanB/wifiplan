import io
import uuid

import pytest
from PIL import Image
from fastapi import HTTPException

from app.models.jobs import Job, JobStatus, JobType
from app.models.project import FloorPlanAsset
from app.models.tenant import Membership, MembershipRole, Organization, User
from app.services.floorplan_upload import _safe_filename, _validate_content
from app.services.parser_base import FloorPlanData


def _create_floor(client, headers, org_id):
    project = client.post(
        f"/api/v1/orgs/{org_id}/projects",
        json={"name": "Tenant project"},
        headers=headers,
    ).json()
    building = client.post(
        f"/api/v1/orgs/{org_id}/projects/{project['id']}/buildings",
        json={"name": "Tenant building"},
        headers=headers,
    ).json()
    floor = client.post(
        f"/api/v1/orgs/{org_id}/projects/{project['id']}/buildings/{building['id']}/floors",
        json={"name": "Tenant floor"},
        headers=headers,
    ).json()
    return project, building, floor


def _user_headers(client, db, org, role=MembershipRole.viewer):
    from app.core.security import hash_password

    user = User(
        email=f"tenant-{uuid.uuid4().hex}@example.com",
        hashed_password=hash_password("TestPass1!"),
        full_name="Tenant test user",
    )
    db.add(user)
    db.flush()
    db.add(Membership(organization_id=org.id, user_id=user.id, role=role))
    db.commit()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "TestPass1!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _png_bytes():
    image = Image.new("RGB", (256, 256), "white")
    data = io.BytesIO()
    image.save(data, format="PNG")
    return data.getvalue()


def test_upload_filename_normalization_removes_path_and_unsafe_characters():
    normalized, extension = _safe_filename("../../Mixed plan!!.png")
    assert normalized == "Mixed-plan.png"
    assert extension == ".png"


def test_upload_filename_validation_rejects_dwg():
    with pytest.raises(HTTPException) as exc:
        _safe_filename("plan.dwg")
    assert exc.value.status_code == 400


def test_upload_content_validation_checks_format_signature():
    _validate_content(_png_bytes(), ".png")
    with pytest.raises(HTTPException):
        _validate_content(b"x" * 200, ".png")


def test_cross_organization_floor_resources_are_forbidden(
    client, db, demo_user, auth_headers
):
    _, _, floor = _create_floor(
        client, auth_headers, str(demo_user["org"].id)
    )
    foreign_org = Organization(
        name="Foreign organization",
        slug=f"foreign-{uuid.uuid4().hex[:10]}",
    )
    db.add(foreign_org)
    db.commit()
    foreign_headers = _user_headers(client, db, foreign_org)

    paths = [
        f"/api/v1/floors/{floor['id']}",
        f"/api/v1/floors/{floor['id']}/geometry",
        f"/api/v1/floors/{floor['id']}/aps",
        f"/api/v1/floors/{floor['id']}/assets",
        f"/api/v1/floors/{floor['id']}/rf/runs",
    ]
    for path in paths:
        response = client.get(path, headers=foreign_headers)
        assert response.status_code == 403, (path, response.text)


def test_viewer_can_read_but_cannot_write_floor_resources(
    client, db, demo_user, auth_headers
):
    _, _, floor = _create_floor(
        client, auth_headers, str(demo_user["org"].id)
    )
    viewer_headers = _user_headers(client, db, demo_user["org"])

    assert client.get(
        f"/api/v1/floors/{floor['id']}", headers=viewer_headers
    ).status_code == 200
    assert client.patch(
        f"/api/v1/floors/{floor['id']}",
        json={"scale_px_per_m": 20},
        headers=viewer_headers,
    ).status_code == 403
    assert client.post(
        f"/api/v1/floors/{floor['id']}/geometry/walls",
        json={
            "geometry": {
                "start": {"x": 0, "y": 0},
                "end": {"x": 1, "y": 1},
            }
        },
        headers=viewer_headers,
    ).status_code == 403


def test_nested_routes_reject_mismatched_ancestry(
    client, demo_user, auth_headers
):
    org_id = str(demo_user["org"].id)
    project_a, _, _ = _create_floor(client, auth_headers, org_id)
    other_project = client.post(
        f"/api/v1/orgs/{org_id}/projects",
        json={"name": "Other project"},
        headers=auth_headers,
    ).json()
    building_b = client.post(
        f"/api/v1/orgs/{org_id}/projects/{other_project['id']}/buildings",
        json={"name": "Other building"},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/api/v1/orgs/{org_id}/projects/{project_a['id']}/buildings/{building_b['id']}/floors",
        json={"name": "Wrong ancestry"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_get_job_requires_membership_in_job_organization(
    client, db, demo_user, auth_headers
):
    job = Job(
        organization_id=demo_user["org"].id,
        created_by=demo_user["user"].id,
        job_type=JobType.rf_simulation,
        status=JobStatus.pending,
        input_payload={},
    )
    db.add(job)
    db.commit()

    foreign_org = Organization(
        name="Job foreign organization",
        slug=f"job-foreign-{uuid.uuid4().hex[:10]}",
    )
    db.add(foreign_org)
    db.commit()
    foreign_headers = _user_headers(client, db, foreign_org)

    response = client.get(f"/api/v1/jobs/{job.id}", headers=foreign_headers)
    assert response.status_code == 403


@pytest.mark.parametrize(
    "filename,content",
    [("plan.png", b"not really a png" * 10), ("../unsafe.png", b"not really a png" * 10)],
)
def test_upload_rejects_content_that_does_not_match_extension(
    client, demo_user, auth_headers, monkeypatch, filename, content
):
    _, _, floor = _create_floor(
        client, auth_headers, str(demo_user["org"].id)
    )
    uploaded = []
    monkeypatch.setattr(
        "app.services.floorplan_upload.storage.upload_bytes",
        lambda *args, **kwargs: uploaded.append(args),
    )
    response = client.post(
        f"/api/v1/floors/{floor['id']}/upload-plan",
        files={"file": (filename, content, "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert uploaded == []


def test_upload_persists_object_before_dispatching_asset_reference(
    client, db, demo_user, auth_headers, monkeypatch
):
    _, _, floor = _create_floor(
        client, auth_headers, str(demo_user["org"].id)
    )
    content = _png_bytes()
    events = []

    def upload_object(bucket, key, data, content_type):
        assert data == content
        events.append(("object", key))

    def parse_file(data, filename, content_type=None):
        assert data == content
        return FloorPlanData(
            walls=[],
            image_width_px=256,
            image_height_px=256,
            source_format="png",
        )

    def enqueue(*args):
        assert len(args) == 1
        assert all(isinstance(arg, str) for arg in args)
        asset = db.query(FloorPlanAsset).filter_by(id=args[0]).one()
        job = db.query(Job).filter(Job.id == asset.processing_job_id).one()
        assert asset.processing_job_id == job.id
        events.append(("task", args))

    monkeypatch.setattr("app.services.floorplan_upload.storage.upload_bytes", upload_object)
    monkeypatch.setattr("app.services.floorplan_upload.ParserFactory.parse", parse_file)
    monkeypatch.setattr("app.services.floorplan_upload.analyze_floor_plan.delay", enqueue)

    response = client.post(
        f"/api/v1/floors/{floor['id']}/upload-plan",
        files={"file": ("../unsafe plan.png", content, "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 202, response.text
    body = response.json()
    assert events[0][0] == "object"
    assert events[1][0] == "task"
    assert "../" not in events[0][1]
    asset = db.query(FloorPlanAsset).filter_by(id=body["asset_id"]).one()
    assert asset.original_filename == "unsafe-plan.png"
    assert asset.s3_key == events[0][1]


def test_failed_task_dispatch_removes_database_rows_and_object(
    client, db, demo_user, auth_headers, monkeypatch
):
    _, _, floor = _create_floor(
        client, auth_headers, str(demo_user["org"].id)
    )
    content = _png_bytes()
    uploaded = []
    deleted = []
    monkeypatch.setattr(
        "app.services.floorplan_upload.storage.upload_bytes",
        lambda bucket, key, data, content_type: uploaded.append(key),
    )
    monkeypatch.setattr(
        "app.services.floorplan_upload.storage.delete_object",
        lambda bucket, key: deleted.append(key),
    )
    monkeypatch.setattr(
        "app.services.floorplan_upload.ParserFactory.parse",
        lambda *args, **kwargs: FloorPlanData(walls=[], source_format="png"),
    )
    monkeypatch.setattr(
        "app.services.floorplan_upload.analyze_floor_plan.delay",
        lambda *args: (_ for _ in ()).throw(RuntimeError("broker unavailable")),
    )

    response = client.post(
        f"/api/v1/floors/{floor['id']}/upload-plan",
        files={"file": ("plan.png", content, "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 500
    assert len(uploaded) == 1
    assert deleted == uploaded
    assert db.query(FloorPlanAsset).filter_by(floor_id=floor["id"]).count() == 0
    assert db.query(Job).filter_by(
        organization_id=demo_user["org"].id,
        job_type=JobType.floor_plan_analysis,
    ).count() == 0
