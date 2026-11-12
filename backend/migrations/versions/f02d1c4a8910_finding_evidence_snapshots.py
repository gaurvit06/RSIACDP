"""retain source references and retrieval times on findings

Revision ID: f02d1c4a8910
Revises: e31b2b999d0f
Create Date: 2026-10-21 03:15:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f02d1c4a8910"
down_revision: Union[str, None] = "e31b2b999d0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("system_findings", sa.Column("evidence_snapshot", sa.JSON(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("system_findings", "evidence_snapshot")
