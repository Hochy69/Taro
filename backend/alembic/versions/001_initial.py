"""Revision ID placeholder - run alembic revision --autogenerate to create migrations."""

from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tables are created via Base.metadata.create_all in development
    # Run: alembic revision --autogenerate -m "initial"
    pass


def downgrade() -> None:
    pass
