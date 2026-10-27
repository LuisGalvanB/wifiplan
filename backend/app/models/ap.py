import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, Float, Integer, ForeignKey, Text, DateTime, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Floor


def utcnow():
    return datetime.now(timezone.utc)


class AntennaType(str, enum.Enum):
    omni = "omni"
    directional = "directional"
    patch = "patch"
    internal = "internal"


class MountType(str, enum.Enum):
    ceiling = "ceiling"
    wall = "wall"
    desktop = "desktop"
    outdoor_pole = "outdoor_pole"


class APVendor(Base):
    __tablename__ = "ap_vendors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    models: Mapped[list["APModel"]] = relationship("APModel", back_populates="vendor")


class APModel(Base):
    __tablename__ = "ap_models"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ap_vendors.id"), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    model_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # RF capabilities
    bands_ghz: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)  # [2.4, 5, 6]
    max_spatial_streams: Mapped[int] = mapped_column(Integer, default=2)
    tx_power_min_dbm: Mapped[float] = mapped_column(Float, default=6.0)
    tx_power_max_dbm: Mapped[float] = mapped_column(Float, default=23.0)
    tx_power_default_dbm: Mapped[float] = mapped_column(Float, default=17.0)

    antenna_type: Mapped[AntennaType] = mapped_column(SAEnum(AntennaType), default=AntennaType.internal)
    antenna_gain_dbi: Mapped[float] = mapped_column(Float, default=3.0)

    mount_type: Mapped[MountType] = mapped_column(SAEnum(MountType), default=MountType.ceiling)
    is_indoor: Mapped[bool] = mapped_column(Boolean, default=True)
    is_outdoor: Mapped[bool] = mapped_column(Boolean, default=False)

    # Display / catalog
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_demo_seed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    vendor: Mapped["APVendor"] = relationship("APVendor", back_populates="models")
    placed_aps: Mapped[list["PlacedAP"]] = relationship("PlacedAP", back_populates="ap_model")


class PlacedAP(Base):
    __tablename__ = "placed_aps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    floor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("floors.id", ondelete="CASCADE"), nullable=False, index=True)
    ap_model_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ap_models.id"), nullable=False)

    label: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g. "AP-01"

    # Position in floor plan pixel space
    x_px: Mapped[float] = mapped_column(Float, nullable=False)
    y_px: Mapped[float] = mapped_column(Float, nullable=False)
    height_m: Mapped[float] = mapped_column(Float, default=2.5)  # above floor

    # RF config
    tx_power_dbm: Mapped[float] = mapped_column(Float, default=17.0)
    bands_active: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)  # subset of model bands

    # Orientation
    azimuth_deg: Mapped[float] = mapped_column(Float, default=0.0)
    tilt_deg: Mapped[float] = mapped_column(Float, default=0.0)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    floor: Mapped["Floor"] = relationship("Floor", back_populates="placed_aps")
    ap_model: Mapped["APModel"] = relationship("APModel", back_populates="placed_aps")
