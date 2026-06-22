"""Add email OTP fields to users table.

Revision ID: 002
Revises: 001
Create Date: 2026-06-22

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add otp_code_hash and otp_expires_at columns to users."""

    op.add_column("users", sa.Column("otp_code_hash", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("otp_expires_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove OTP columns from users."""

    op.drop_column("users", "otp_expires_at")
    op.drop_column("users", "otp_code_hash")
