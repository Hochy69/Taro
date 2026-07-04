"""Add profile birth details and lunar day cache."""

from alembic import op
import sqlalchemy as sa

revision = "005_profile_extras"
down_revision = "004_add_referrals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("birth_time", sa.String(8), nullable=True))
    op.add_column("profiles", sa.Column("birth_city", sa.String(120), nullable=True))
    op.add_column("profiles", sa.Column("gender", sa.String(1), nullable=True))
    op.add_column("profiles", sa.Column("lunar_birth_day", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("profiles", "lunar_birth_day")
    op.drop_column("profiles", "gender")
    op.drop_column("profiles", "birth_city")
    op.drop_column("profiles", "birth_time")
