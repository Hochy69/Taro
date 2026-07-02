"""Add terms_accepted_at to users (one-time offer/terms acceptance)."""

from alembic import op
import sqlalchemy as sa

revision = "002_add_terms_accepted"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "terms_accepted_at")
