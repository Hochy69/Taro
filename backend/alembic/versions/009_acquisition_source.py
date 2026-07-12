"""Add partner/ad acquisition attribution fields."""

import sqlalchemy as sa
from alembic import op

revision = "009_acquisition_source"
down_revision = "008_marketing_pushes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("acquisition_source", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_users_acquisition_source", "users", ["acquisition_source"])
    op.create_table(
        "acquisition_pending",
        sa.Column("telegram_id", sa.BigInteger(), primary_key=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_acquisition_pending_source", "acquisition_pending", ["source"])


def downgrade() -> None:
    op.drop_index("ix_acquisition_pending_source", table_name="acquisition_pending")
    op.drop_table("acquisition_pending")
    op.drop_index("ix_users_acquisition_source", table_name="users")
    op.drop_column("users", "acquisition_source")
