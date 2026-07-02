"""Add is_admin flag to users (hidden admin access via /admin secret word)."""

from alembic import op
import sqlalchemy as sa

revision = "003_add_is_admin"
down_revision = "002_add_terms_accepted"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("users", "is_admin")
