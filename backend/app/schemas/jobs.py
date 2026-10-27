from pydantic import BaseModel
import uuid
from datetime import datetime
from app.models.jobs import JobType, JobStatus


class JobOut(BaseModel):
    id: uuid.UUID
    job_type: JobType
    status: JobStatus
    progress_pct: int
    progress_message: str | None
    error_message: str | None
    result_payload: dict | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class RFSimulationRequest(BaseModel):
    band_ghz: str = "5"  # "2.4", "5", "6"
    grid_resolution_px: int = 10


class RFSimulationRunOut(BaseModel):
    id: uuid.UUID
    floor_id: uuid.UUID
    band_ghz: str
    grid_resolution_px: int
    heatmap_width: int | None
    heatmap_height: int | None
    heatmap_s3_key: str | None
    coverage_good_pct: float | None
    coverage_fair_pct: float | None
    coverage_poor_pct: float | None
    min_rssi_dbm: float | None
    max_rssi_dbm: float | None
    avg_rssi_dbm: float | None
    created_at: datetime

    model_config = {"from_attributes": True}
