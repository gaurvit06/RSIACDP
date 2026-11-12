"""persist versioned claim-level machine findings

Revision ID: e31b2b999d0f
Revises: d1c77aa03521
Create Date: 2026-10-21 03:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e31b2b999d0f"
down_revision: Union[str, None] = "d1c77aa03521"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_id", sa.Integer(), sa.ForeignKey("entities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("assessment", sa.String(length=64), nullable=False),
        sa.Column("observation", sa.Text(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("conflict_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("rule_name", sa.String(length=80), nullable=False),
        sa.Column("rule_version", sa.String(length=40), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_system_findings_case_id", "system_findings", ["case_id"])
    op.create_index("ix_system_findings_entity_id", "system_findings", ["entity_id"])
    op.create_index("ix_system_findings_active", "system_findings", ["active"])


def downgrade() -> None:
    op.drop_index("ix_system_findings_active", table_name="system_findings")
    op.drop_index("ix_system_findings_entity_id", table_name="system_findings")
    op.drop_index("ix_system_findings_case_id", table_name="system_findings")
    op.drop_table("system_findings")
