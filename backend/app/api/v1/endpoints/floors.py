
# wifiplan/backend/app/api/v1/endpoints/floors.py

"""
Direct floor operations by floor_id — used by the planner when org/project/building
context isn't needed (e.g. scale calibration, floor metadata fetch).
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.api.deps import get_current_user, require_floor_access
from app.models.tenant import User, MembershipRole
from app.schemas.project import FloorOut, FloorUpdate
from app.services.floorplan_upload import create_floor_plan_upload

# Crear router
router = APIRouter(prefix="/floors", tags=["floors"])

@router.get("/{floor_id}", response_model=FloorOut)
def get_floor(
    floor_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get floor details by ID."""
    return require_floor_access(floor_id, user, db)


@router.patch("/{floor_id}", response_model=FloorOut)
def update_floor(
    floor_id: str,
    payload: FloorUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Direct floor patch — used by scale calibration modal."""
    floor = require_floor_access(floor_id, user, db, MembershipRole.editor)
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(floor, k, v)
    db.commit()
    db.refresh(floor)
    return floor


@router.post("/{floor_id}/upload-plan", status_code=202)
async def upload_floor_plan(
    floor_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Upload a floor plan image or vector file for analysis.
    
    Supported formats:
    - Raster: PNG, JPG, JPEG
    - Vector: DXF
    - Document: PDF (converted to image)
    
    Returns a job_id for polling the analysis status.
    """
    floor = require_floor_access(floor_id, user, db, MembershipRole.editor)
    return await create_floor_plan_upload(floor, user, file, db)