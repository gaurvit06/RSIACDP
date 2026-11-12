"""persist privacy-minimal login throttle buckets

Revision ID: c96cc6d17573
Revises: b6a6c0192de4
Create Date: 2026-10-21 04:30:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c96cc6d17573"
down_revision: Union[str, None] = "b6a6c0192de4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "login_throttles",
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("window_started_at", sa.Float(), nullable=False),
        sa.Column("locked_until", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("fingerprint"),
    )

def downgrade() -> None:
    op.drop_table("login_throttles")
