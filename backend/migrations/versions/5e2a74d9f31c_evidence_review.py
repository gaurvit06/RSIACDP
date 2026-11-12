"""persist evidence relevance review

Revision ID: 5e2a74d9f31c
Revises: 748ef602ab07
Create Date: 2026-10-21 01:56:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5e2a74d9f31c"
down_revision: Union[str, None] = "748ef602ab07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("evidence") as batch_op:
        batch_op.add_column(sa.Column("review_status", sa.String(length=24), server_default="unreviewed", nullable=False))
        batch_op.add_column(sa.Column("review_reason", sa.Text(), server_default="", nullable=False))
        batch_op.add_column(sa.Column("reviewed_by", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key("fk_evidence_reviewed_by_users", "users", ["reviewed_by"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("evidence") as batch_op:
        batch_op.drop_constraint("fk_evidence_reviewed_by_users", type_="foreignkey")
        batch_op.drop_column("reviewed_at")
        batch_op.drop_column("reviewed_by")
        batch_op.drop_column("review_reason")
        batch_op.drop_column("review_status")
