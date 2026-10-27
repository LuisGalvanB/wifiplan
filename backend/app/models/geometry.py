# backend/app/models/geometry.py

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, Float, ForeignKey, DateTime, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Floor


def utcnow():
    return datetime.now(timezone.utc)


class MaterialType(str, enum.Enum):
    # ordered roughly by attenuation (low to high)
    glass = "glass"
    drywall = "drywall"
    wood = "wood"
    brick = "brick"
    concrete = "concrete"
    metal = "metal"
    unknown = "unknown"


# Attenuation values in dB per wall pass — MVP heuristic defaults
MATERIAL_ATTENUATION = {
    # band: {material: dB}
    "2.4": {
        MaterialType.glass: 2.0,
        MaterialType.drywall: 3.5,
        MaterialType.wood: 4.0,
        MaterialType.brick: 8.0,
        MaterialType.concrete: 12.0,
        MaterialType.metal: 15.0,
        MaterialType.unknown: 5.0,
    },
    "5": {
        MaterialType.glass: 3.0,
        MaterialType.drywall: 5.0,
        MaterialType.wood: 6.0,
        MaterialType.brick: 12.0,
        MaterialType.concrete: 16.0,
        MaterialType.metal: 20.0,
        MaterialType.unknown: 7.0,
    },
    "6": {
        MaterialType.glass: 3.5,
        MaterialType.drywall: 6.0,
        MaterialType.wood: 7.0,
        MaterialType.brick: 14.0,
        MaterialType.concrete: 18.0,
        MaterialType.metal: 22.0,
        MaterialType.unknown: 8.0,
    },
}


class WallType(str, enum.Enum):
    exterior = "exterior"
    interior = "interior"
    partition = "partition"
    column = "column"
    unknown = "unknown"


class GeometrySourceType(str, enum.Enum):
    manual = "manual"
    cv_detected = "cv_detected"
    ml_detected = "ml_detected"
    imported = "imported"


class Wall(Base):
    __tablename__ = "walls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    floor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("floors.id", ondelete="CASCADE"), nullable=False, index=True)

    # Geometry: stored as pixel coords relative to floor plan image
    # {start: {x,y}, end: {x,y}} — line segment pair
    geometry: Mapped[dict] = mapped_column(JSONB, nullable=False)

    wall_type: Mapped[WallType] = mapped_column(SAEnum(WallType), default=WallType.unknown)
    material: Mapped[MaterialType] = mapped_column(SAEnum(MaterialType), default=MaterialType.unknown)
    thickness_px: Mapped[float] = mapped_column(Float, default=5.0)
    height_m: Mapped[float] = mapped_column(Float, default=2.8)

    # --- NUEVOS CAMPOS para el sistema multi-formato ---
    # source_type: origen del dato (vectorial, raster, manual)
    source_type: Mapped[str] = mapped_column(String(50), default="manual")
    # thickness_m: espesor real en metros (extraído de DXF o estimado)
    thickness_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    # confidence: nivel de confianza (1.0 = 100%, <1.0 = estimado)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    # Custom attenuation overrides (overrides material defaults if set)
    attenuation_2_4ghz_db: Mapped[float | None] = mapped_column(Float, nullable=True)
    attenuation_5ghz_db: Mapped[float | None] = mapped_column(Float, nullable=True)
    attenuation_6ghz_db: Mapped[float | None] = mapped_column(Float, nullable=True)

    # source: cómo se creó la geometría (manual/cv_detected/ml_detected/imported)
    source: Mapped[GeometrySourceType] = mapped_column(SAEnum(GeometrySourceType), default=GeometrySourceType.manual)
    is_accepted: Mapped[bool] = mapped_column(Boolean, default=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    floor: Mapped["Floor"] = relationship("Floor", back_populates="walls")

    def get_attenuation(self, band: str) -> float:
        """Return effective attenuation dB for this wall at given band."""
        override = {
            "2.4": self.attenuation_2_4ghz_db,
            "5": self.attenuation_5ghz_db,
            "6": self.attenuation_6ghz_db,
        }.get(band)
        if override is not None:
            return override
        return MATERIAL_ATTENUATION.get(band, {}).get(self.material, 5.0)


class OpeningType(str, enum.Enum):
    door = "door"
    window = "window"
    opening = "opening"


class Opening(Base):
    __tablename__ = "openings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    floor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("floors.id", ondelete="CASCADE"), nullable=False, index=True)
    wall_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("walls.id", ondelete="SET NULL"), nullable=True)
    opening_type: Mapped[OpeningType] = mapped_column(SAEnum(OpeningType), default=OpeningType.door)
    geometry: Mapped[dict] = mapped_column(JSONB, nullable=False)  # {start:{x,y}, end:{x,y}}
    source: Mapped[GeometrySourceType] = mapped_column(SAEnum(GeometrySourceType), default=GeometrySourceType.manual)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    floor: Mapped["Floor"] = relationship("Floor", back_populates="openings")


class ObstacleType(str, enum.Enum):
    rack = "rack"
    shelf = "shelf"
    column = "column"
    elevator = "elevator"
    stairwell = "stairwell"
    hvac = "hvac"
    generic = "generic"


class Obstacle(Base):
    __tablename__ = "obstacles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    floor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("floors.id", ondelete="CASCADE"), nullable=False, index=True)
    obstacle_type: Mapped[ObstacleType] = mapped_column(SAEnum(ObstacleType), default=ObstacleType.generic)
    # Polygon geometry: [{x, y}, ...]
    geometry: Mapped[dict] = mapped_column(JSONB, nullable=False)  # {points: [{x,y},...]}
    height_m: Mapped[float] = mapped_column(Float, default=2.0)
    material: Mapped[MaterialType] = mapped_column(SAEnum(MaterialType), default=MaterialType.metal)
    source: Mapped[GeometrySourceType] = mapped_column(SAEnum(GeometrySourceType), default=GeometrySourceType.manual)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    floor: Mapped["Floor"] = relationship("Floor", back_populates="obstacles")


class ScopeZone(Base):
    __tablename__ = "scope_zones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    floor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("floors.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), default="Coverage Zone")
    # Polygon: {points: [{x,y},...]}
    geometry: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source: Mapped[GeometrySourceType] = mapped_column(SAEnum(GeometrySourceType), default=GeometrySourceType.manual)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    floor: Mapped["Floor"] = relationship("Floor", back_populates="scope_zones")
