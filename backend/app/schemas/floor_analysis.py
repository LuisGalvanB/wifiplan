# backend/app/schemas/floor_analysis.py

"""
Pydantic schemas for floor plan analysis results.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.parser_base import (
    WallClassification,
    WallSourceType,
)


class WallOut(BaseModel):
    """Wall returned by the floor analysis API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    floor_id: uuid.UUID

    # Expected structure:
    # {
    #     "start": {"x": 0.0, "y": 0.0},
    #     "end": {"x": 1.0, "y": 1.0},
    # }
    geometry: Dict[str, Any]

    wall_type: WallClassification
    material: str

    thickness_px: Optional[float] = None
    thickness_m: Optional[float] = None

    source: WallSourceType
    confidence: float = Field(ge=0.0, le=1.0)

    is_accepted: bool
    created_at: datetime
    
    # --- NUEVO: Para compatibilidad con el modelo existente ---
    # El modelo de base de datos tiene 'source_type' (string) y 'wall_type' (enum)
    # pero el schema usa 'source' (WallSourceType) y 'wall_type' (WallClassification)
    
    @field_validator('source', mode='before')
    @classmethod
    def validate_source(cls, v):
        """Convertir string a WallSourceType si es necesario."""
        if isinstance(v, str):
            mapping = {
                "manual": WallSourceType.UNKNOWN,
                "vectorial": WallSourceType.VECTORIAL,
                "raster": WallSourceType.RASTER,
                "cv_detected": WallSourceType.RASTER,
                "ml_detected": WallSourceType.RASTER,
                "imported": WallSourceType.UNKNOWN,
            }
            return mapping.get(v.lower(), WallSourceType.UNKNOWN)
        return v
    
    @field_validator('wall_type', mode='before')
    @classmethod
    def validate_wall_type(cls, v):
        """Convertir WallType del modelo a WallClassification del schema."""
        if isinstance(v, str):
            mapping = {
                "exterior": WallClassification.LOAD_BEARING,
                "interior": WallClassification.PARTITION,
                "partition": WallClassification.PARTITION,
                "column": WallClassification.UNKNOWN,
                "unknown": WallClassification.UNKNOWN,
            }
            return mapping.get(v.lower(), WallClassification.UNKNOWN)
        # Si es un enum, convertirlo
        if hasattr(v, 'value'):
            value = v.value
            mapping = {
                "exterior": WallClassification.LOAD_BEARING,
                "interior": WallClassification.PARTITION,
                "partition": WallClassification.PARTITION,
                "column": WallClassification.UNKNOWN,
                "unknown": WallClassification.UNKNOWN,
            }
            return mapping.get(value, WallClassification.UNKNOWN)
        return v
    
    # --- Opcional: Property para compatibilidad con frontend ---
    @property
    def source_type(self) -> str:
        """Alias para compatibilidad con frontend que espera 'source_type'."""
        return self.source.value if hasattr(self.source, 'value') else str(self.source)
    
    @property
    def wall_type_str(self) -> str:
        """Obtener wall_type como string para el frontend."""
        return self.wall_type.value if hasattr(self.wall_type, 'value') else str(self.wall_type)


class FloorAnalysisResult(BaseModel):
    """Complete result of a floor-plan analysis process."""

    model_config = ConfigDict(from_attributes=True)

    floor_id: uuid.UUID
    walls: List[WallOut]

    scope_zones: Optional[List[Dict[str, Any]]] = None

    # Examples: png, jpg, jpeg, pdf, dxf.
    source_format: str

    # Examples: mm, cm, m, inches, px.
    drawing_unit: Optional[str] = None

    image_width_px: Optional[int] = Field(default=None, ge=1)
    image_height_px: Optional[int] = Field(default=None, ge=1)

    processing_time_ms: Optional[int] = Field(default=None, ge=0)

    metadata: Dict[str, Any] = Field(default_factory=dict)