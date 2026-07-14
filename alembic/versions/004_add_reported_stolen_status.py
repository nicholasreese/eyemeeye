"""Add reported_stolen value to phonestatus enum.

Revision ID: 004
Revises: 003
Create Date: 2026-07-14

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add reported_stolen to the phonestatus enum type."""

    op.execute(sa.text("ALTER TYPE phonestatus ADD VALUE IF NOT EXISTS 'reported_stolen' BEFORE 'disposed'"))


def downgrade() -> None:
    """PostgreSQL does not support removing enum values; downgrade is a no-op."""
