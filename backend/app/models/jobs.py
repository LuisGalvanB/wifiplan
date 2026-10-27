import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, Float, Integer, ForeignKey, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Floor


def utcnow():
    return datetime.now(timezone.utc)


class JobType(str, enum.Enum):
    floor_plan_analysis = "floor_plan_analysis"
    rf_simulation = "rf_simulation"
    report_generation = "report_generation"


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    job_type: Mapped[JobType] = mapped_column(SAEnum(JobType), nullable=False)
    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), default=JobStatus.pending, index=True)

    celery_task_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Input/output payloads
    input_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    progress_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RFSimulationRun(Base):
    __tablename__ = "rf_simulation_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    floor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("floors.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)

    band_ghz: Mapped[str] = mapped_column(String(10), nullable=False)  # "2.4", "5", "6"
    grid_resolution_px: Mapped[int] = mapped_column(Integer, default=10)

    # Stored heatmap — numpy array serialized as flat list with dimensions
    heatmap_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    heatmap_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    heatmap_s3_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Summary stats
    coverage_good_pct: Mapped[float | None] = mapped_column(Float, nullable=True)   # RSSI >= -65
    coverage_fair_pct: Mapped[float | None] = mapped_column(Float, nullable=True)   # RSSI -65 to -75
    coverage_poor_pct: Mapped[float | None] = mapped_column(Float, nullable=True)   # RSSI < -75
    min_rssi_dbm: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_rssi_dbm: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_rssi_dbm: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    floor: Mapped["Floor"] = relationship("Floor", back_populates="rf_simulation_runs")
