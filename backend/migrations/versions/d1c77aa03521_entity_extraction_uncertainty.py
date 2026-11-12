"""persist entity extraction confidence and uncertainty

Revision ID: d1c77aa03521
Revises: c42a7a34d781
Create Date: 2026-10-21 02:15:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1c77aa03521"
down_revision: Union[str, None] = "c42a7a34d781"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("entities") as batch_op:
        batch_op.add_column(sa.Column("extraction_confidence", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("extraction_uncertainty", sa.String(length=300), server_default="", nullable=False))


def downgrade() -> None:
    with op.batch_alter_table("entities") as batch_op:
        batch_op.drop_column("extraction_uncertainty")
        batch_op.drop_column("extraction_confidence")
