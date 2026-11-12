"""persist two-person human disposition review

Revision ID: a63b9d024ae1
Revises: 8f35d5a2b6c1
Create Date: 2026-10-21 03:02:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a63b9d024ae1"
down_revision: Union[str, None] = "8f35d5a2b6c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "human_dispositions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("disposition", sa.String(length=40), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=24), server_default="recorded", nullable=False),
        sa.Column("proposed_by", sa.Integer(), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("review_rationale", sa.Text(), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["proposed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_human_dispositions_case_id"), "human_dispositions", ["case_id"], unique=False)
    op.create_index(op.f("ix_human_dispositions_status"), "human_dispositions", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_human_dispositions_status"), table_name="human_dispositions")
    op.drop_index(op.f("ix_human_dispositions_case_id"), table_name="human_dispositions")
    op.drop_table("human_dispositions")
