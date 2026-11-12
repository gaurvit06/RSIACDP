"""persist text spans for extracted entities

Revision ID: 8f35d5a2b6c1
Revises: 5e2a74d9f31c
Create Date: 2026-10-21 02:06:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f35d5a2b6c1"
down_revision: Union[str, None] = "5e2a74d9f31c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("entities") as batch_op:
        batch_op.add_column(sa.Column("source_location", sa.String(length=80), server_default="submitted_text", nullable=False))
        batch_op.add_column(sa.Column("source_start_char", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("source_end_char", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("entities") as batch_op:
        batch_op.drop_column("source_end_char")
        batch_op.drop_column("source_start_char")
        batch_op.drop_column("source_location")
