"""Alembic environment configuration with Flask-SQLAlchemy integration."""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool

# Ensure the project root is importable so src.app can be resolved.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

load_dotenv()

alembic_config = context.config

if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# Allow DATABASE_URL env var to override alembic.ini so local, CI, and
# production environments each use the right connection string.
database_url = os.getenv("DATABASE_URL", "sqlite:///app.db")
# psycopg v3 requires the postgresql+psycopg:// dialect prefix; rewrite bare postgresql:// URLs.
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
alembic_config.set_main_option("sqlalchemy.url", database_url)

# Importing models registers their tables with db.metadata.
from src.app.extensions import db  # noqa: E402
import src.app.models  # noqa: E402, F401

target_metadata = db.metadata


def run_migrations_offline() -> None:
    """Run migrations without an active DB connection (generates SQL)."""

    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""

    connectable = create_engine(
        alembic_config.get_main_option("sqlalchemy.url"),  # type: ignore[arg-type]
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
