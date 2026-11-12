"""persist retryable Neo4j projection work

Revision ID: d84f8a1a5301
Revises: c96cc6d17573
Create Date: 2026-10-21 16:10:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d84f8a1a5301"
down_revision: Union[str, None] = "c96cc6d17573"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "graph_projection_outbox",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        # Deliberately not a foreign key: delete tombstones outlive the case row.
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("operation", sa.String(length=12), server_default="upsert", nullable=False),
        sa.Column("generation", sa.Integer(), server_default="1", nullable=False),
        sa.Column("status", sa.String(length=16), server_default="queued", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_error", sa.Text(), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", name="uq_graph_projection_case"),
    )
    op.create_index("ix_graph_projection_outbox_case_id", "graph_projection_outbox", ["case_id"])
    op.create_index("ix_graph_projection_outbox_status", "graph_projection_outbox", ["status"])
    op.create_index("ix_graph_projection_outbox_available_at", "graph_projection_outbox", ["available_at"])


def downgrade() -> None:
    op.drop_index("ix_graph_projection_outbox_available_at", table_name="graph_projection_outbox")
    op.drop_index("ix_graph_projection_outbox_status", table_name="graph_projection_outbox")
    op.drop_index("ix_graph_projection_outbox_case_id", table_name="graph_projection_outbox")
    op.drop_table("graph_projection_outbox")
