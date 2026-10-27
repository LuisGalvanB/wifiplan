from pydantic import BaseModel
import uuid
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    address: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    address: str | None = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None
    address: str | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BuildingCreate(BaseModel):
    name: str


class BuildingOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FloorCreate(BaseModel):
    name: str
    level: int = 0
    floor_height_m: float = 3.0
    ceiling_height_m: float = 2.8


class FloorUpdate(BaseModel):
    name: str | None = None
    level: int | None = None
    floor_height_m: float | None = None
    ceiling_height_m: float | None = None
    scale_px_per_m: float | None = None


class FloorOut(BaseModel):
    id: uuid.UUID
    building_id: uuid.UUID
    name: str
    level: int
    floor_height_m: float
    ceiling_height_m: float
    scale_px_per_m: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FloorPlanAssetOut(BaseModel):
    id: uuid.UUID
    floor_id: uuid.UUID
    original_filename: str
    s3_key: str
    content_type: str
    width_px: int | None
    height_px: int | None
    file_size_bytes: int | None
    processing_job_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
