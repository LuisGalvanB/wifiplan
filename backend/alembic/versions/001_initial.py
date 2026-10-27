"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # organizations
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # memberships
    op.create_table(
        "memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="editor"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # jobs (before floor_plan_assets FK)
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("celery_task_id", sa.String(200), nullable=True),
        sa.Column("input_payload", postgresql.JSONB(), nullable=True),
        sa.Column("result_payload", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progress_message", sa.String(500), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_organization_id", "jobs", ["organization_id"])

    # projects
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_organization_id", "projects", ["organization_id"])

    # buildings
    op.create_table(
        "buildings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # floors
    op.create_table(
        "floors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("building_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("floor_height_m", sa.Float(), nullable=False, server_default="3.0"),
        sa.Column("ceiling_height_m", sa.Float(), nullable=False, server_default="2.8"),
        sa.Column("scale_px_per_m", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # floor_plan_assets
    op.create_table(
        "floor_plan_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("floor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("s3_key", sa.String(1000), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("width_px", sa.Integer(), nullable=True),
        sa.Column("height_px", sa.Integer(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("processing_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["processing_job_id"], ["jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_floor_plan_assets_floor_id", "floor_plan_assets", ["floor_id"])

    # walls
    op.create_table(
        "walls",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("floor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("geometry", postgresql.JSONB(), nullable=False),
        sa.Column("wall_type", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("material", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("thickness_px", sa.Float(), nullable=False, server_default="5.0"),
        sa.Column("height_m", sa.Float(), nullable=False, server_default="2.8"),
        sa.Column("attenuation_2_4ghz_db", sa.Float(), nullable=True),
        sa.Column("attenuation_5ghz_db", sa.Float(), nullable=True),
        sa.Column("attenuation_6ghz_db", sa.Float(), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("is_accepted", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_walls_floor_id", "walls", ["floor_id"])

    # openings
    op.create_table(
        "openings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("floor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("wall_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("opening_type", sa.String(20), nullable=False, server_default="door"),
        sa.Column("geometry", postgresql.JSONB(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["wall_id"], ["walls.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # obstacles
    op.create_table(
        "obstacles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("floor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("obstacle_type", sa.String(20), nullable=False, server_default="generic"),
        sa.Column("geometry", postgresql.JSONB(), nullable=False),
        sa.Column("height_m", sa.Float(), nullable=False, server_default="2.0"),
        sa.Column("material", sa.String(20), nullable=False, server_default="metal"),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # scope_zones
    op.create_table(
        "scope_zones",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("floor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False, server_default="Coverage Zone"),
        sa.Column("geometry", postgresql.JSONB(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ap_vendors
    op.create_table(
        "ap_vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(50), nullable=False),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )

    # ap_models
    op.create_table(
        "ap_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_name", sa.String(200), nullable=False),
        sa.Column("model_number", sa.String(100), nullable=True),
        sa.Column("bands_ghz", postgresql.JSONB(), nullable=False),
        sa.Column("max_spatial_streams", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("tx_power_min_dbm", sa.Float(), nullable=False),
        sa.Column("tx_power_max_dbm", sa.Float(), nullable=False),
        sa.Column("tx_power_default_dbm", sa.Float(), nullable=False),
        sa.Column("antenna_type", sa.String(20), nullable=False, server_default="internal"),
        sa.Column("antenna_gain_dbi", sa.Float(), nullable=False, server_default="3.0"),
        sa.Column("mount_type", sa.String(20), nullable=False, server_default="ceiling"),
        sa.Column("is_indoor", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_outdoor", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_demo_seed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["vendor_id"], ["ap_vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ap_models_vendor_id", "ap_models", ["vendor_id"])

    # placed_aps
    op.create_table(
        "placed_aps",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("floor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ap_model_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column("x_px", sa.Float(), nullable=False),
        sa.Column("y_px", sa.Float(), nullable=False),
        sa.Column("height_m", sa.Float(), nullable=False, server_default="2.5"),
        sa.Column("tx_power_dbm", sa.Float(), nullable=False, server_default="17.0"),
        sa.Column("bands_active", postgresql.JSONB(), nullable=False),
        sa.Column("azimuth_deg", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("tilt_deg", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ap_model_id"], ["ap_models.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_placed_aps_floor_id", "placed_aps", ["floor_id"])

    # rf_simulation_runs
    op.create_table(
        "rf_simulation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("floor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("band_ghz", sa.String(10), nullable=False),
        sa.Column("grid_resolution_px", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("heatmap_width", sa.Integer(), nullable=True),
        sa.Column("heatmap_height", sa.Integer(), nullable=True),
        sa.Column("heatmap_s3_key", sa.String(1000), nullable=True),
        sa.Column("coverage_good_pct", sa.Float(), nullable=True),
        sa.Column("coverage_fair_pct", sa.Float(), nullable=True),
        sa.Column("coverage_poor_pct", sa.Float(), nullable=True),
        sa.Column("min_rssi_dbm", sa.Float(), nullable=True),
        sa.Column("max_rssi_dbm", sa.Float(), nullable=True),
        sa.Column("avg_rssi_dbm", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rf_simulation_runs_floor_id", "rf_simulation_runs", ["floor_id"])


def downgrade() -> None:
    op.drop_table("rf_simulation_runs")
    op.drop_table("placed_aps")
    op.drop_table("ap_models")
    op.drop_table("ap_vendors")
    op.drop_table("scope_zones")
    op.drop_table("obstacles")
    op.drop_table("openings")
    op.drop_table("walls")
    op.drop_table("floor_plan_assets")
    op.drop_table("floors")
    op.drop_table("buildings")
    op.drop_table("projects")
    op.drop_table("jobs")
    op.drop_table("memberships")
    op.drop_table("users")
    op.drop_table("organizations")
