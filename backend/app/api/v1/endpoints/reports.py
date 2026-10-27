#backend>app>api>v1>endpoints>reports.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.api.deps import get_current_user, require_project_access
from app.models.tenant import User
from app.models.project import Building, Floor, FloorPlanAsset
from app.models.geometry import Wall
from app.models.ap import PlacedAP
from app.models.jobs import RFSimulationRun

router = APIRouter(prefix="/orgs/{org_id}/projects/{project_id}/report", tags=["reports"])


@router.get("/json")
def export_json_report(
    org_id: str,
    project_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Export a complete project report as JSON.
    Future: trigger PDF generation job.
    """
    project = require_project_access(project_id, org_id, user, db)

    buildings = db.query(Building).filter(Building.project_id == project_id).all()

    buildings_data = []
    for b in buildings:
        floors = db.query(Floor).filter(Floor.building_id == b.id).order_by(Floor.level).all()
        floors_data = []
        for f in floors:
            wall_count = db.query(Wall).filter(Wall.floor_id == f.id).count()
            ap_count = db.query(PlacedAP).filter(PlacedAP.floor_id == f.id).count()
            asset_count = db.query(FloorPlanAsset).filter(FloorPlanAsset.floor_id == f.id).count()

            # Latest RF run per floor
            latest_rf = (
                db.query(RFSimulationRun)
                .filter(RFSimulationRun.floor_id == f.id)
                .order_by(RFSimulationRun.created_at.desc())
                .first()
            )

            rf_summary = None
            if latest_rf:
                rf_summary = {
                    "band_ghz": latest_rf.band_ghz,
                    "coverage_good_pct": latest_rf.coverage_good_pct,
                    "coverage_fair_pct": latest_rf.coverage_fair_pct,
                    "coverage_poor_pct": latest_rf.coverage_poor_pct,
                    "avg_rssi_dbm": latest_rf.avg_rssi_dbm,
                    "run_date": latest_rf.created_at.isoformat(),
                }

            # AP inventory
            placed_aps = db.query(PlacedAP).filter(PlacedAP.floor_id == f.id).all()
            ap_inventory = []
            for ap in placed_aps:
                model = ap.ap_model
                ap_inventory.append({
                    "label": ap.label,
                    "model": model.model_name if model else "Unknown",
                    "vendor": model.vendor.name if model and model.vendor else "Unknown",
                    "x_px": ap.x_px,
                    "y_px": ap.y_px,
                    "tx_power_dbm": ap.tx_power_dbm,
                    "bands": ap.bands_active,
                })

            floors_data.append({
                "id": str(f.id),
                "name": f.name,
                "level": f.level,
                "scale_px_per_m": f.scale_px_per_m,
                "wall_count": wall_count,
                "ap_count": ap_count,
                "floor_plan_uploaded": asset_count > 0,
                "rf_summary": rf_summary,
                "ap_inventory": ap_inventory,
            })

        buildings_data.append({
            "id": str(b.id),
            "name": b.name,
            "floors": floors_data,
        })

    return {
        "project": {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "address": project.address,
            "created_at": project.created_at.isoformat(),
        },
        "buildings": buildings_data,
        "report_generated_at": __import__("datetime").datetime.utcnow().isoformat(),
        "report_version": "1.0",
        # PDF generation: stub — future task would call a headless browser or reportlab
        "_pdf_note": "PDF export: trigger POST /report/pdf (not yet implemented)",
    }
