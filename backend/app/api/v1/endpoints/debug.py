# backend/app/api/v1/endpoints/debug.py

"""
Debug endpoints for floor geometry.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.api.deps import get_current_user
from app.models.tenant import User
from app.models.geometry import Wall

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/floors/{floor_id}/walls/confidence-summary")
def get_confidence_summary(
    floor_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a summary of wall confidence levels for a floor."""
    walls = db.query(Wall).filter(Wall.floor_id == floor_id).all()
    
    summary = {
        "total": len(walls),
        "confidence_1_0": 0,
        "confidence_high": 0,  # >= 0.7 y < 1.0
        "confidence_low": 0,   # < 0.7
        "by_source_type": {}
    }
    
    for wall in walls:
        # Estadísticas por confianza
        if wall.confidence == 1.0:
            summary["confidence_1_0"] += 1
        elif wall.confidence >= 0.7:
            summary["confidence_high"] += 1
        else:
            summary["confidence_low"] += 1
        
        # Estadísticas por source_type
        source = wall.source_type or "unknown"
        summary["by_source_type"][source] = summary["by_source_type"].get(source, 0) + 1
    
    return summary