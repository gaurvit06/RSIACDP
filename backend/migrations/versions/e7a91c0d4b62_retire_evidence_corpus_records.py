"""allow reviewer withdrawal of curated evidence records

Revision ID: e7a91c0d4b62
Revises: c28f4e6a1b93
Create Date: 2026-10-26 10:50:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7a91c0d4b62"
down_revision: Union[str, None] = "c28f4e6a1b93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("source_records") as batch:
        batch.add_column(sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False))
        batch.add_column(sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("retired_by", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("retirement_reason", sa.Text(), server_default="", nullable=False))
        batch.create_foreign_key(
            "fk_source_records_retired_by_users",
            "users",
            ["retired_by"],
            ["id"],
        )
        batch.create_index("ix_source_records_active", ["active"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("source_records") as batch:
        batch.drop_index("ix_source_records_active")
        batch.drop_constraint("fk_source_records_retired_by_users", type_="foreignkey")
        batch.drop_column("retirement_reason")
        batch.drop_column("retired_by")
        batch.drop_column("retired_at")
        batch.drop_column("active")
