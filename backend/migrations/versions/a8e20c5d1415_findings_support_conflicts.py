"""record support, contradiction, and pending evidence links on findings

Revision ID: a8e20c5d1415
Revises: f02d1c4a8910
Create Date: 2026-10-21 03:30:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a8e20c5d1415"
down_revision: Union[str, None] = "f02d1c4a8910"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("system_findings") as batch_op:
        batch_op.add_column(sa.Column("supporting_evidence_ids", sa.JSON(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("unreviewed_evidence_ids", sa.JSON(), nullable=False, server_default="[]"))


def downgrade() -> None:
    with op.batch_alter_table("system_findings") as batch_op:
        batch_op.drop_column("unreviewed_evidence_ids")
        batch_op.drop_column("supporting_evidence_ids")
