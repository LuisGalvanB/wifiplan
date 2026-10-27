import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.api.deps import get_current_user, require_organization_access, require_floor_access
from app.models.tenant import User, MembershipRole
from app.models.jobs import Job, JobType, JobStatus, RFSimulationRun
from app.schemas.jobs import JobOut, RFSimulationRequest, RFSimulationRunOut
from app.services import storage
from app.core.config import settings

jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])
rf_router = APIRouter(prefix="/floors/{floor_id}/rf", tags=["rf-simulation"])
logger = logging.getLogger(__name__)


@jobs_router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    require_organization_access(str(job.organization_id), user, db)
    return job


@rf_router.post("/simulate", response_model=dict, status_code=202)
def trigger_rf_simulation(
    floor_id: str,
    payload: RFSimulationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Enqueue an RF simulation job. Returns job_id for polling."""
    floor = require_floor_access(floor_id, user, db, MembershipRole.editor)

    org_id = floor.building.project.organization_id

    job = Job(
        organization_id=org_id,
        created_by=user.id,
        job_type=JobType.rf_simulation,
        status=JobStatus.pending,
        input_payload={
            "floor_id": floor_id,
            "band": payload.band_ghz,
            "grid_res": payload.grid_resolution_px,
        },
    )
    db.add(job)
    db.commit()

    from app.workers.tasks import run_rf_simulation
    try:
        run_rf_simulation.delay(str(job.id), floor_id, payload.band_ghz, payload.grid_resolution_px)
    except Exception as exc:
        logger.exception("Unable to enqueue RF simulation job %s", job.id)
        job.status = JobStatus.failed
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = "RF simulation could not be queued"
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="RF simulation could not be queued. Please retry.",
        ) from exc

    return {"job_id": str(job.id), "message": "RF simulation queued"}


@rf_router.get("/runs", response_model=list[RFSimulationRunOut])
def list_rf_runs(
    floor_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_floor_access(floor_id, user, db)
    return (
        db.query(RFSimulationRun)
        .filter(RFSimulationRun.floor_id == floor_id)
        .order_by(RFSimulationRun.created_at.desc())
        .all()
    )


@rf_router.get("/runs/{run_id}/heatmap-url")
def get_heatmap_url(
    floor_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_floor_access(floor_id, user, db)
    run = db.query(RFSimulationRun).filter(
        RFSimulationRun.id == run_id,
        RFSimulationRun.floor_id == floor_id,
    ).first()
    if not run:
        raise HTTPException(404, "Simulation run not found")
    if not run.heatmap_s3_key:
        raise HTTPException(404, "Heatmap not yet available")

    url = storage.get_presigned_url(settings.S3_BUCKET_HEATMAPS, run.heatmap_s3_key)
    return {"url": url, "expires_in": 3600}
