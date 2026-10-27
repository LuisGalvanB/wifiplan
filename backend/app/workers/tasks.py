# backend/app/workers/tasks.py

"""
Celery worker tasks.

Each task:
1. Updates job status in DB at start and end
2. Runs the heavy computation (CV pipeline or RF engine)
3. Persists results (geometry to DB, heatmap to S3)
4. Updates job with final status and result_payload
"""
import uuid
import logging
from datetime import datetime, timezone

from celery import Task
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.db.base import SessionLocal
from app.models.jobs import Job, JobStatus, RFSimulationRun
from app.models.geometry import Wall, GeometrySourceType, MaterialType
from app.models.ap import PlacedAP
from app.models.project import Floor, FloorPlanAsset
from app.services import storage
from app.core.config import settings
from app.services.factory import ParserFactory
from app.services.parsers.wall_conversion import (
    classification_to_wall_type,
    source_type_to_string
)

logger = logging.getLogger(__name__)


def _get_db() -> Session:
    return SessionLocal()


def _update_job(db: Session, job_id: str, **kwargs):
    """Update job status and progress."""
    job = db.query(Job).filter(Job.id == uuid.UUID(job_id)).first()
    if job:
        for k, v in kwargs.items():
            setattr(job, k, v)
        db.commit()


def _utcnow():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


# ──────────────────────────────────────────────────────────────────────────────
# 1. FLOOR PLAN ANALYSIS (multi-format: PNG, JPG, PDF, DXF)
# ──────────────────────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True, 
    name="app.workers.tasks.analyze_floor_plan",
    queue="cv_pipeline",
    max_retries=2
)
def analyze_floor_plan(
    self: Task,
    asset_id: str,
):
    """
    Async floor plan analysis task supporting multiple formats.
    
    Supported formats:
    - Raster: PNG, JPG, JPEG
    - Vector: DXF
    - Document: PDF (converted to image)
    
    Flow:
    1. Load the uploaded object from storage through its asset reference
    2. Use ParserFactory to detect format and parse
    3. Save walls and scope zones to DB
    4. Mark job completed with result summary
    """
    db = _get_db()
    job = None
    
    try:
        # 1. Load the persisted asset and its linked job using the sole queue reference.
        asset = db.query(FloorPlanAsset).filter(
            FloorPlanAsset.id == uuid.UUID(asset_id),
        ).first()
        if not asset:
            raise ValueError(f"Floor-plan asset {asset_id} not found")
        if not asset.processing_job_id:
            raise ValueError(f"Floor-plan asset {asset_id} has no processing job")
        job = db.query(Job).filter(Job.id == asset.processing_job_id).first()
        if not job:
            raise ValueError(f"Job for floor-plan asset {asset_id} not found")
        job_id = str(job.id)

        floor = db.query(Floor).filter(Floor.id == asset.floor_id).first()
        if not floor or floor.building.project.organization_id != job.organization_id:
            raise ValueError("Floor-plan asset organization mismatch")

        _update_job(db, job_id,
            status=JobStatus.running,
            started_at=_utcnow(),
            celery_task_id=self.request.id,
            progress_pct=10,
            progress_message="Starting floor plan analysis",
        )
        
        # 2. Fetch content using the stored object key; payloads remain out of Celery.
        _update_job(db, job_id, progress_pct=20, progress_message="Loading uploaded floor plan")
        file_content = storage.download_bytes(settings.S3_BUCKET_FLOORPLANS, asset.s3_key)

        # 3. Parsear usando factory
        _update_job(db, job_id, progress_pct=40, progress_message="Parsing uploaded floor plan")
        parsed_data = ParserFactory.parse(file_content, asset.original_filename, asset.content_type)

        # 4. Save detected walls.
        _update_job(db, job_id, progress_pct=70, progress_message="Saving detected walls")
        
        walls_created = 0
        for w in parsed_data.walls:
            # Convertir tipos usando los helpers
            wall_type = classification_to_wall_type(w.classification)
            source_type_str = source_type_to_string(w.source_type)
            
            # Determinar GeometrySourceType según source_type
            if source_type_str == "vectorial":
                geometry_source = GeometrySourceType.imported
            elif source_type_str == "raster":
                geometry_source = GeometrySourceType.cv_detected
            else:
                geometry_source = GeometrySourceType.manual
            
            wall = Wall(
                floor_id=floor.id,
                geometry={
                    "start": {"x": w.start_x, "y": w.start_y},
                    "end": {"x": w.end_x, "y": w.end_y},
                },
                wall_type=wall_type,
                material=MaterialType.unknown,
                thickness_m=w.thickness_m,
                source_type=source_type_str,  # "vectorial", "raster", o "manual"
                confidence=w.confidence,
                is_accepted=False,  # Requiere revisión del usuario
                created_by=job.created_by,
                source=geometry_source,  # imported, cv_detected, o manual
            )
            db.add(wall)
            walls_created += 1
        
        # 5. Save scope zone if supported by the parser.
        scope_created = 0
        # TODO: Cuando ParserFactory soporte scope_zones, añadir:
        # if hasattr(parsed_data, 'scope_zones') and parsed_data.scope_zones:
        #     for sz in parsed_data.scope_zones:
        #         scope = ScopeZone(
        #             floor_id=floor_id,
        #             name="Detected Perimeter",
        #             geometry=sz["geometry"],
        #             source=GeometrySourceType.cv_detected,
        #             confidence=sz.get("confidence", 0.65),
        #         )
        #         db.add(scope)
        #         scope_created += 1
        
        db.commit()
        
        # 6. Mark the job completed.
        result_payload = {
            "walls_added": walls_created,
            "source_format": parsed_data.source_format,
            "drawing_unit": parsed_data.drawing_unit,
            "image_width_px": parsed_data.image_width_px,
            "image_height_px": parsed_data.image_height_px,
            "scope_zones_detected": scope_created,
        }
        
        _update_job(db, job_id,
            status=JobStatus.completed,
            completed_at=_utcnow(),
            progress_pct=100,
            progress_message=f"Complete: {walls_created} walls detected",
            result_payload=result_payload,
        )
        
        logger.info("Floor plan analysis completed: floor=%s, walls=%s", floor.id, walls_created)
        return result_payload
        
    except Exception as exc:
        logger.exception(f"Floor plan analysis failed for job {job_id}")
        
        # Actualizar job con error
        if job:
            _update_job(db, job_id,
                status=JobStatus.failed,
                completed_at=_utcnow(),
                error_message="Floor-plan processing failed",
                progress_pct=0,
                progress_message="Floor-plan processing failed",
            )
        
        # Reintentar si es un error recuperable
        if isinstance(exc, (ValueError, TypeError, UnicodeDecodeError)):
            # Errores de datos no se reintentan
            raise exc
        else:
            raise self.retry(exc=exc, countdown=10, max_retries=2)
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────────────────────
# 2. RF SIMULATION (heatmap computation)
# ──────────────────────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_rf_simulation",
    queue="rf_engine",
    max_retries=1
)
def run_rf_simulation(
    self: Task,
    job_id: str,
    floor_id: str,
    band: str,
    grid_res: int,
):
    """
    Async RF heatmap computation task.

    Flow:
    1. Load floor geometry and placed APs from DB
    2. Compute heatmap using RF engine
    3. Render to PNG and upload to S3
    4. Persist RFSimulationRun with stats
    """
    db = _get_db()
    try:
        _update_job(db, job_id,
            status=JobStatus.running,
            started_at=_utcnow(),
            celery_task_id=self.request.id,
            progress_pct=10,
            progress_message="Loading floor geometry",
        )

        floor = db.query(Floor).filter(Floor.id == uuid.UUID(floor_id)).first()
        if not floor:
            raise ValueError(f"Floor {floor_id} not found")

        # Determine image dimensions from latest asset
        asset = (
            db.query(FloorPlanAsset)
            .filter(FloorPlanAsset.floor_id == floor.id)
            .order_by(FloorPlanAsset.created_at.desc())
            .first()
        )

        width_px = asset.width_px if asset and asset.width_px else 1000
        height_px = asset.height_px if asset and asset.height_px else 1000
        scale_px_per_m = floor.scale_px_per_m or 20.0  # default: 20px = 1m

        # Load walls
        walls_db = db.query(Wall).filter(Wall.floor_id == floor.id).all()

        from app.services.rf_engine import Seg, APPoint, compute_heatmap, compute_coverage_stats, heatmap_to_rgba_png

        wall_segs = []
        for w in walls_db:
            g = w.geometry
            atten = w.get_attenuation(band)
            wall_segs.append(Seg(
                x1=g["start"]["x"], y1=g["start"]["y"],
                x2=g["end"]["x"],   y2=g["end"]["y"],
                attenuation_db=atten,
            ))

        # Load placed APs
        placed = db.query(PlacedAP).filter(PlacedAP.floor_id == floor.id).all()
        ap_points = []
        for ap in placed:
            model = ap.ap_model
            ap_points.append(APPoint(
                x_px=ap.x_px,
                y_px=ap.y_px,
                tx_power_dbm=ap.tx_power_dbm,
                antenna_gain_dbi=model.antenna_gain_dbi if model else 3.0,
            ))

        if not ap_points:
            # No APs — return empty heatmap
            _update_job(db, job_id,
                status=JobStatus.completed,
                completed_at=_utcnow(),
                progress_pct=100,
                progress_message="No APs placed — empty heatmap",
                result_payload={"warning": "no_aps"},
            )
            return {"warning": "no_aps"}

        _update_job(db, job_id, progress_pct=40, progress_message="Computing heatmap")

        heatmap = compute_heatmap(
            width_px=width_px,
            height_px=height_px,
            scale_px_per_m=scale_px_per_m,
            aps=ap_points,
            wall_segs=wall_segs,
            band=band,
            grid_res=grid_res,
        )

        stats = compute_coverage_stats(heatmap)

        _update_job(db, job_id, progress_pct=75, progress_message="Rendering heatmap image")

        # Render to PNG
        png_bytes = heatmap_to_rgba_png(heatmap)
        s3_key = f"heatmaps/{floor_id}/{band}_{job_id}.png"
        storage.upload_bytes(settings.S3_BUCKET_HEATMAPS, s3_key, png_bytes, "image/png")

        # Persist run record
        gh, gw = heatmap.shape
        run = RFSimulationRun(
            floor_id=floor.id,
            job_id=uuid.UUID(job_id),
            band_ghz=band,
            grid_resolution_px=grid_res,
            heatmap_width=gw,
            heatmap_height=gh,
            heatmap_s3_key=s3_key,
            **stats,
        )
        db.add(run)
        db.commit()

        result_payload = {"run_id": str(run.id), **stats}

        _update_job(db, job_id,
            status=JobStatus.completed,
            completed_at=_utcnow(),
            progress_pct=100,
            progress_message="RF simulation complete",
            result_payload=result_payload,
        )

        return result_payload

    except Exception as exc:
        logger.exception(f"RF simulation failed for job {job_id}")
        _update_job(db, job_id,
            status=JobStatus.failed,
            completed_at=_utcnow(),
            error_message="RF simulation failed",
        )
        raise self.retry(exc=exc, countdown=5)
    finally:
        db.close()