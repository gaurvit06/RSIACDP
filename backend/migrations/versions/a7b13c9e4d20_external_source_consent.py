"""record separate consent for optional RDAP checks

Revision ID: a7b13c9e4d20
Revises: 9a4c1e7d2b60
Create Date: 2026-10-21 17:10:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b13c9e4d20"
down_revision: Union[str, None] = "9a4c1e7d2b60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("external_source_consent", sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade() -> None:
    op.drop_column("cases", "external_source_consent")
