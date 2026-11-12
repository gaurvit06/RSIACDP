"""capture worker execution duration for reproducible evaluation

Revision ID: c28f4e6a1b93
Revises: f19c7b2a8d45
Create Date: 2026-10-25 00:50:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c28f4e6a1b93"
down_revision: Union[str, None] = "f19c7b2a8d45"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column("processing_jobs", sa.Column("processing_ms", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("processing_jobs", "processing_ms")
