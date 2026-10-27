# backend/app/schemas/geometry.py
"""Pydantic schemas for geometry returned by direct floor operations."""

import uuid

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.geometry import (
    GeometrySourceType,
    MaterialType,
    ObstacleType,
    OpeningType,
    WallType,
)


class Point(BaseModel):
    """Two-dimensional point."""

    x: float
    y: float


class WallGeometry(BaseModel):
    """Wall represented by its start and end points."""

    start: Point
    end: Point


class PolygonGeometry(BaseModel):
    """Polygon represented by an ordered collection of points."""

    points: list[Point]


class WallCreate(BaseModel):
    """Payload used to create a wall."""

    geometry: WallGeometry
    wall_type: WallType = WallType.unknown
    material: MaterialType = MaterialType.unknown

    thickness_px: float = Field(default=5.0, gt=0)
    thickness_m: float | None = Field(default=None, gt=0)
    height_m: float = Field(default=2.8, gt=0)

    attenuation_2_4ghz_db: float | None = Field(default=None, ge=0)
    attenuation_5ghz_db: float | None = Field(default=None, ge=0)
    attenuation_6ghz_db: float | None = Field(default=None, ge=0)

    source: GeometrySourceType = GeometrySourceType.manual
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class WallUpdate(BaseModel):
    """Payload used to update a wall partially."""

    geometry: WallGeometry | None = None
    wall_type: WallType | None = None
    material: MaterialType | None = None

    thickness_px: float | None = Field(default=None, gt=0)
    thickness_m: float | None = Field(default=None, gt=0)
    height_m: float | None = Field(default=None, gt=0)

    attenuation_2_4ghz_db: float | None = Field(default=None, ge=0)
    attenuation_5ghz_db: float | None = Field(default=None, ge=0)
    attenuation_6ghz_db: float | None = Field(default=None, ge=0)

    source: GeometrySourceType | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    is_accepted: bool | None = None


class WallOut(BaseModel):
    """Wall returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    floor_id: uuid.UUID
    geometry: dict[str, Any]

    wall_type: WallType
    material: MaterialType

    thickness_px: float
    thickness_m: float | None = None
    height_m: float

    attenuation_2_4ghz_db: float | None = None
    attenuation_5ghz_db: float | None = None
    attenuation_6ghz_db: float | None = None

    source: GeometrySourceType
    confidence: float | None = None
    is_accepted: bool

    created_at: datetime


class WallBulkCreate(BaseModel):
    """Payload used to create multiple walls."""

    walls: list[WallCreate]


class WallBulkOut(BaseModel):
    """Result of bulk wall creation."""

    created: int
    walls: list[WallOut]


class OpeningCreate(BaseModel):
    """Payload used to create an opening."""

    geometry: WallGeometry
    opening_type: OpeningType = OpeningType.door
    wall_id: uuid.UUID | None = None
    source: GeometrySourceType = GeometrySourceType.manual
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class OpeningOut(BaseModel):
    """Opening returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    floor_id: uuid.UUID
    wall_id: uuid.UUID | None = None

    opening_type: OpeningType
    geometry: dict[str, Any]
    source: GeometrySourceType
    confidence: float | None = None

    created_at: datetime


class ObstacleCreate(BaseModel):
    """Payload used to create an obstacle."""

    geometry: PolygonGeometry
    obstacle_type: ObstacleType = ObstacleType.generic
    height_m: float = Field(default=2.0, gt=0)
    material: MaterialType = MaterialType.metal

    source: GeometrySourceType = GeometrySourceType.manual
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class ObstacleOut(BaseModel):
    """Obstacle returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    floor_id: uuid.UUID
    obstacle_type: ObstacleType
    geometry: dict[str, Any]

    height_m: float
    material: MaterialType
    source: GeometrySourceType
    confidence: float | None = None

    created_at: datetime


class ScopeZoneCreate(BaseModel):
    """Payload used to create a coverage zone."""

    name: str = Field(
        default="Coverage Zone",
        min_length=1,
        max_length=255,
    )

    geometry: PolygonGeometry
    source: GeometrySourceType = GeometrySourceType.manual
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class ScopeZoneOut(BaseModel):
    """Coverage zone returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    floor_id: uuid.UUID
    name: str
    geometry: dict[str, Any]

    source: GeometrySourceType
    confidence: float | None = None

    created_at: datetime


class FloorGeometryOut(BaseModel):
    """Complete geometry for a floor."""

    floor_id: uuid.UUID
    walls: list[WallOut] = Field(default_factory=list)
    openings: list[OpeningOut] = Field(default_factory=list)
    obstacles: list[ObstacleOut] = Field(default_factory=list)
    scope_zones: list[ScopeZoneOut] = Field(default_factory=list)