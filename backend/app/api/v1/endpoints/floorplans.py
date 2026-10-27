# backend/app/api/v1/endpoints/floorplans.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.api.deps import get_current_user, require_floor_access
from app.models.tenant import User, MembershipRole
from app.models.project import FloorPlanAsset
from app.schemas.project import FloorPlanAssetOut
from app.services import storage
from app.services.floorplan_upload import create_floor_plan_upload
from app.core.config import settings


router = APIRouter(prefix="/floors/{floor_id}", tags=["floor-plans"])


@router.post("/upload", status_code=202)
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


@router.get("/assets", response_model=list[FloorPlanAssetOut])
def list_assets(
    floor_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_floor_access(floor_id, user, db)
    return db.query(FloorPlanAsset).filter(FloorPlanAsset.floor_id == floor_id).all()


@router.get("/assets/{asset_id}/url")
def get_asset_url(
    floor_id: str,
    asset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_floor_access(floor_id, user, db)
    asset = db.query(FloorPlanAsset).filter(
        FloorPlanAsset.id == asset_id,
        FloorPlanAsset.floor_id == floor_id,
    ).first()
    if not asset:
        raise HTTPException(404, "Asset not found")
    
    url = storage.get_presigned_url(settings.S3_BUCKET_FLOORPLANS, asset.s3_key)
    return {"url": url, "expires_in": 3600}
