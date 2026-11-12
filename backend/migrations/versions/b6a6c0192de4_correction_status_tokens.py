"""store one-way hashes for correction status access tokens

Revision ID: b6a6c0192de4
Revises: a8e20c5d1415
Create Date: 2026-10-21 04:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b6a6c0192de4"
down_revision: Union[str, None] = "a8e20c5d1415"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("correction_requests", sa.Column("status_token_hash", sa.String(length=64), nullable=False, server_default=""))

def downgrade() -> None:
    op.drop_column("correction_requests", "status_token_hash")
