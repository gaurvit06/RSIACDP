"""add user session revocation version

Revision ID: c42a7a34d781
Revises: a63b9d024ae1
Create Date: 2026-10-21 03:18:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c42a7a34d781"
down_revision: Union[str, None] = "a63b9d024ae1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("token_version", sa.Integer(), server_default="0", nullable=False))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("token_version")
