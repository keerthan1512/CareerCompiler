"""
Alembic environment configuration.
Uses synchronous psycopg2 driver for migrations (standard pattern).
The async engine is used by the application at runtime.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import all models to ensure they are registered with Base.metadata
# Add new model imports here as phases progress
from src.database import Base
from src.models.user import User  # noqa: F401
from src.models.master_resume import MasterResume  # noqa: F401
from src.models.canonical_profile import CanonicalProfile  # noqa: F401
from src.models.audit_log import AuditLog  # noqa: F401
from src.models.parse_job import ParseJob  # noqa: F401

config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    """
    Get the sync database URL from environment.
    Converts asyncpg URL to psycopg2 URL for Alembic.
    """
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://ccuser:ccpassword@localhost:5432/careercompiler",
    )
    # Convert asyncpg URL to psycopg2 for synchronous Alembic
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL without DB connection)."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects to DB)."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
