"""Add marketing push notification enum values."""

from alembic import op

revision = "008_marketing_pushes"
down_revision = "007_promo_codes"
branch_labels = None
depends_on = None

_NEW_VALUES = [
    "START_NO_WEBAPP",
    "SPREAD_FIRST",
    "SPREAD_SECOND",
    "SPREAD_THIRD",
    "FREE_LIMIT_HIT",
    "FREE_LIMIT_FOLLOWUP",
    "COMPAT_VIEW_ABANDONED",
    "COMPAT_PAID_UPSELL",
    "WEEKLY_REFERRAL",
]


def upgrade() -> None:
    for value in _NEW_VALUES:
        op.execute(f"ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    pass
