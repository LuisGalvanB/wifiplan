"""Shared floor-plan upload workflow for direct and nested floor routes."""
import logging
import re
import unicodedata
import uuid
from pathlib import PurePosixPath

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.jobs import Job, JobStatus, JobType
from app.models.project import Floor, FloorPlanAsset
from app.models.tenant import User
from app.services import storage
from app.services.factory import ParserFactory
from app.workers.tasks import analyze_floor_plan

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".dxf"}
CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".pdf": "application/pdf",
    ".dxf": "application/dxf",
}


def _safe_filename(filename: str | None) -> tuple[str, str]:
    raw_name = (filename or "").replace("\\", "/")
    basename = unicodedata.normalize("NFKC", PurePosixPath(raw_name).name)
    ext = PurePosixPath(basename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported floor-plan file format")

    stem = basename[: -len(PurePosixPath(basename).suffix)]
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", stem).strip("-_")
    stem = (stem or "floor-plan")[:160]
    return f"{stem}{ext}", ext


def _validate_content(content: bytes, ext: str) -> None:
    if len(content) < 100:
        raise HTTPException(status_code=400, detail="File is empty or invalid")
    signatures = {
        ".png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": content.startswith(b"\xff\xd8\xff"),
        ".jpeg": content.startswith(b"\xff\xd8\xff"),
        ".pdf": content.startswith(b"%PDF-"),
    }
    if ext in signatures and not signatures[ext]:
        raise HTTPException(status_code=400, detail="File content does not match its file format")


async def create_floor_plan_upload(
    floor: Floor,
    user: User,
    file: UploadFile,
    db: Session,
) -> dict:
    safe_filename, ext = _safe_filename(file.filename)
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds the 50 MB limit")
    _validate_content(content, ext)

    try:
        parsed = ParserFactory.parse(content, safe_filename, CONTENT_TYPES[ext])
    except ValueError:
        logger.info("Rejected invalid floor-plan content for floor %s", floor.id)
        raise HTTPException(status_code=400, detail="File content is invalid or unsupported")
    except Exception:
        logger.exception("Floor-plan validation failed for floor %s", floor.id)
        raise HTTPException(status_code=400, detail="File content is invalid or unsupported")

    organization_id = floor.building.project.organization_id
    object_key = (
        f"organizations/{organization_id}/floors/{floor.id}/"
        f"{uuid.uuid4().hex}-{safe_filename}"
    )
    job = None
    asset = None
    object_upload_attempted = False

    try:
        object_upload_attempted = True
        storage.upload_bytes(
            settings.S3_BUCKET_FLOORPLANS,
            object_key,
            content,
            CONTENT_TYPES[ext],
        )
        job = Job(
            organization_id=organization_id,
            created_by=user.id,
            job_type=JobType.floor_plan_analysis,
            status=JobStatus.pending,
            input_payload={
                "floor_id": str(floor.id),
                "asset_id": None,
                "source_format": parsed.source_format,
                "detected_walls": len(parsed.walls),
            },
        )
        db.add(job)
        db.flush()
        asset = FloorPlanAsset(
            floor_id=floor.id,
            original_filename=safe_filename,
            s3_key=object_key,
            content_type=CONTENT_TYPES[ext],
            width_px=parsed.image_width_px,
            height_px=parsed.image_height_px,
            file_size_bytes=len(content),
            processing_job_id=job.id,
        )
        db.add(asset)
        db.flush()
        job.input_payload = {
            **job.input_payload,
            "asset_id": str(asset.id),
        }
        db.commit()
        db.refresh(job)
        db.refresh(asset)

        # Workers fetch the persisted object via the asset; file bytes never enter the queue.
        analyze_floor_plan.delay(str(asset.id))
        return {
            "job_id": str(job.id),
            "floor_id": str(floor.id),
            "message": "Floor plan analysis started",
            "source_format": parsed.source_format,
            "detected_walls": len(parsed.walls),
            "asset_id": str(asset.id),
        }
    except Exception:
        logger.exception("Floor-plan upload failed for floor %s", floor.id)
        db.rollback()

        # A committed row set may need cleanup if task dispatch failed.
        try:
            if asset is not None:
                db.query(FloorPlanAsset).filter(FloorPlanAsset.id == asset.id).delete(
                    synchronize_session=False
                )
            if job is not None:
                db.query(Job).filter(Job.id == job.id).delete(synchronize_session=False)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Could not roll back floor-plan rows for floor %s", floor.id)

        if object_upload_attempted:
            try:
                storage.delete_object(settings.S3_BUCKET_FLOORPLANS, object_key)
            except Exception:
                logger.exception("Could not remove failed floor-plan object for floor %s", floor.id)
        raise HTTPException(status_code=500, detail="Floor-plan upload could not be completed")
