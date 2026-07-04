"""Profile astrology extras + daily card push preference."""

from alembic import op
import sqlalchemy as sa

revision = "006_astrology_phase2"
down_revision = "005_profile_extras"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("birth_lat", sa.Float(), nullable=True))
    op.add_column("profiles", sa.Column("birth_lon", sa.Float(), nullable=True))
    op.add_column("profiles", sa.Column("birth_timezone", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("daily_card_push", sa.Boolean(), server_default="true", nullable=False))


def downgrade() -> None:
    op.drop_column("users", "daily_card_push")
    op.drop_column("profiles", "birth_timezone")
    op.drop_column("profiles", "birth_lon")
    op.drop_column("profiles", "birth_lat")
