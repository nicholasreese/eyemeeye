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

from src.app.utils.db_url import build_database_url  # noqa: E402

# Build the URL once; do NOT pass it to set_main_option — ConfigParser rejects % chars
# (percent-encoded passwords trigger invalid interpolation syntax errors).
database_url = build_database_url(
    os.getenv("DATABASE_URL", "sqlite:///app.db"),
    os.getenv("DB_PASSWORD", ""),
)

# Importing models registers their tables with db.metadata.
from src.app.extensions import db  # noqa: E402
import src.app.models  # noqa: E402, F401

target_metadata = db.metadata


def run_migrations_offline() -> None:
    """Run migrations without an active DB connection (generates SQL)."""

    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""

    connectable = create_engine(
        database_url,
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
