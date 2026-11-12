"""serialize one-time investigator and reviewer account provisioning

Revision ID: f19c7b2a8d45
Revises: a7b13c9e4d20
Create Date: 2026-10-23 18:10:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f19c7b2a8d45"
down_revision: Union[str, None] = "a7b13c9e4d20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "account_provisioning_gates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("generation", sa.Integer(), server_default="0", nullable=False),
    )
    op.bulk_insert(
        sa.table(
            "account_provisioning_gates",
            sa.column("id", sa.Integer()),
            sa.column("generation", sa.Integer()),
        ),
        [{"id": 1, "generation": 0}],
    )


def downgrade() -> None:
    op.drop_table("account_provisioning_gates")
