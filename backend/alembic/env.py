#wifiplan\backend\alembic\env.py
"""
Alembic migration environment for WifiPlan.

This configuration:

- Uses DATABASE_URL from the application settings.
- Loads all SQLAlchemy models into Base.metadata.
- Limits autogeneration to WifiPlan application tables.
- Ignores PostGIS, Tiger Geocoder, and Topology internal tables.
- Prevents unwanted automatic conversions between VARCHAR and PostgreSQL ENUM.
"""

import os
import sys
from logging.config import fileConfig
from typing import Any

from alembic import context
from sqlalchemy import engine_from_config, pool


# ---------------------------------------------------------------------------
# Python path
# ---------------------------------------------------------------------------

# Directory containing this file:
# /app/alembic
ALEMBIC_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Backend root:
# /app
BACKEND_ROOT = os.path.dirname(ALEMBIC_DIRECTORY)

if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)


# ---------------------------------------------------------------------------
# Application imports
# ---------------------------------------------------------------------------

from app.core.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402

# This import must load all SQLAlchemy models so that Alembic can inspect
# their tables through Base.metadata.
import app.models  # noqa: E402, F401


# ---------------------------------------------------------------------------
# Alembic configuration
# ---------------------------------------------------------------------------

config = context.config


def get_database_url() -> str:
    """
    Return the database URL configured for the current environment.

    In Docker, the expected value is:

    postgresql://wifiplan:wifiplan@postgres:5432/wifiplan

    Outside Docker, localhost may be used instead.
    """

    environment_url = os.getenv("DATABASE_URL")

    if environment_url:
        return environment_url

    configured_url = getattr(settings, "DATABASE_URL", None)

    if configured_url is None:
        configured_url = getattr(settings, "database_url", None)

    if configured_url is None:
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Define it in the environment or in app.core.config.settings."
        )

    return str(configured_url)


DATABASE_URL = get_database_url()

# Override sqlalchemy.url from alembic.ini.
config.set_main_option("sqlalchemy.url", DATABASE_URL)


# Configure Python logging using alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# SQLAlchemy metadata used by Alembic autogeneration.
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Application tables
# ---------------------------------------------------------------------------

# Only these tables are owned and managed by WifiPlan.
#
# Limiting Alembic to this allowlist prevents autogeneration from producing
# DROP TABLE operations for PostGIS, Tiger Geocoder, and Topology objects.
APP_TABLES = {
    "organizations",
    "users",
    "memberships",
    "jobs",
    "projects",
    "buildings",
    "floors",
    "floor_plan_assets",
    "walls",
    "openings",
    "obstacles",
    "scope_zones",
    "ap_vendors",
    "ap_models",
    "placed_aps",
    "rf_simulation_runs",
}


# Internal or extension-managed schemas that Alembic must ignore.
IGNORED_SCHEMAS = {
    "information_schema",
    "pg_catalog",
    "tiger",
    "tiger_data",
    "topology",
}


def include_name(
    name: str | None,
    type_: str,
    parent_names: dict[str, Any],
) -> bool:
    """
    Filter schemas and tables during Alembic reflection.

    Alembic is allowed to inspect only the public schema and the application
    tables explicitly listed in APP_TABLES.
    """

    if type_ == "schema":
        # The default PostgreSQL schema may be represented by None.
        return name in {None, "public"}

    schema_name = parent_names.get("schema_name")

    if schema_name in IGNORED_SCHEMAS:
        return False

    if type_ == "table":
        return name in APP_TABLES

    return True


def include_object(
    object_: Any,
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to: Any,
) -> bool:
    """
    Apply an additional safety filter to reflected database objects.

    This prevents extension-owned tables from being interpreted as obsolete
    application tables.
    """

    if type_ == "table":
        schema_name = getattr(object_, "schema", None)

        if schema_name in IGNORED_SCHEMAS:
            return False

        return name in APP_TABLES

    return True


# ---------------------------------------------------------------------------
# Offline migrations
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Run migrations without creating a live database connection.

    This mode is used by commands such as:

        alembic upgrade head --sql
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        include_name=include_name,
        include_object=include_object,
        include_schemas=False,

        # Disabled temporarily because the initial schema created several
        # columns as VARCHAR while the SQLAlchemy models use Python enums.
        # Enabling this now would generate many unrelated ALTER COLUMN
        # operations.
        compare_type=False,

        # Avoid generating unrelated changes for defaults defined differently
        # between SQLAlchemy and PostgreSQL.
        compare_server_default=False,

        version_table="alembic_version",
        version_table_schema=None,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations
# ---------------------------------------------------------------------------

def run_migrations_online() -> None:
    """
    Run migrations using a live SQLAlchemy database connection.
    """

    configuration = config.get_section(
        config.config_ini_section,
        {},
    )

    configuration["sqlalchemy.url"] = DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_name=include_name,
            include_object=include_object,
            include_schemas=False,

            # See the explanation in run_migrations_offline().
            compare_type=False,
            compare_server_default=False,

            version_table="alembic_version",
            version_table_schema=None,
        )

        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
