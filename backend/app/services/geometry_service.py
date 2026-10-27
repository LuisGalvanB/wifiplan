# backend/app/services/geometry_service.py

"""
Service for geometry operations.
"""
from sqlalchemy.orm import Session
from app.models.geometry import Wall


def get_walls_by_source_type(db: Session, floor_id: str, source_type: str) -> list[Wall]:
    """
    Get walls by source type for a specific floor.
    
    Args:
        db: Database session
        floor_id: Floor ID
        source_type: "vectorial", "raster", or "manual"
    
    Returns:
        List of walls
    """
    return db.query(Wall).filter(
        Wall.floor_id == floor_id,
        Wall.source_type == source_type
    ).all()


def get_vectorial_walls(db: Session, floor_id: str) -> list[Wall]:
    """Get walls from DXF files."""
    return get_walls_by_source_type(db, floor_id, "vectorial")


def get_raster_walls(db: Session, floor_id: str) -> list[Wall]:
    """Get walls from raster files (images/PDF)."""
    return get_walls_by_source_type(db, floor_id, "raster")


def get_walls_by_confidence(db: Session, floor_id: str, min_confidence: float = 0.7) -> list[Wall]:
    """Get walls with confidence above a threshold."""
    return db.query(Wall).filter(
        Wall.floor_id == floor_id,
        Wall.confidence >= min_confidence
    ).all()