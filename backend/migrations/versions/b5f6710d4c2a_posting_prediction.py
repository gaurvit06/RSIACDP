"""Store the posting classifier's versioned decision separately from source findings."""
from alembic import op
import sqlalchemy as sa

revision = "b5f6710d4c2a"
down_revision = "e7a91c0d4b62"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("cases", sa.Column("posting_prediction", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("cases", "posting_prediction")
