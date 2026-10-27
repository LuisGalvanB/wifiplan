import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, Float, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.ap import PlacedAP
    from app.models.geometry import Obstacle, Opening, ScopeZone, Wall
    from app.models.jobs import RFSimulationRun
    from app.models.tenant import Organization


def utcnow():
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="projects")
    buildings: Mapped[list["Building"]] = relationship("Building", back_populates="project", cascade="all, delete-orphan")


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="buildings")
    floors: Mapped[list["Floor"]] = relationship("Floor", back_populates="building", cascade="all, delete-orphan")


class Floor(Base):
    __tablename__ = "floors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    building_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0)  # 0 = ground floor
    floor_height_m: Mapped[float] = mapped_column(Float, default=3.0)
    ceiling_height_m: Mapped[float] = mapped_column(Float, default=2.8)
    scale_px_per_m: Mapped[float | None] = mapped_column(Float, nullable=True)  # set after calibration
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    building: Mapped["Building"] = relationship("Building", back_populates="floors")
    floor_plan_assets: Mapped[list["FloorPlanAsset"]] = relationship("FloorPlanAsset", back_populates="floor")
    walls: Mapped[list["Wall"]] = relationship("Wall", back_populates="floor", cascade="all, delete-orphan")
    openings: Mapped[list["Opening"]] = relationship("Opening", back_populates="floor", cascade="all, delete-orphan")
    obstacles: Mapped[list["Obstacle"]] = relationship("Obstacle", back_populates="floor", cascade="all, delete-orphan")
    scope_zones: Mapped[list["ScopeZone"]] = relationship("ScopeZone", back_populates="floor", cascade="all, delete-orphan")
    placed_aps: Mapped[list["PlacedAP"]] = relationship("PlacedAP", back_populates="floor", cascade="all, delete-orphan")
    rf_simulation_runs: Mapped[list["RFSimulationRun"]] = relationship("RFSimulationRun", back_populates="floor")


class FloorPlanAsset(Base):
    __tablename__ = "floor_plan_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    floor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("floors.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    width_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    floor: Mapped["Floor"] = relationship("Floor", back_populates="floor_plan_assets")
