"""Add marketing push notification enum values."""

from alembic import op

revision = "008_marketing_pushes"
down_revision = "007_promo_codes"
branch_labels = None
depends_on = None

_NEW_VALUES = [
    "start_no_webapp",
    "spread_first",
    "spread_second",
    "spread_third",
    "free_limit_hit",
    "free_limit_followup",
    "compat_view_abandoned",
    "compat_paid_upsell",
    "weekly_referral",
]


def upgrade() -> None:
    for value in _NEW_VALUES:
        op.execute(f"ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    pass
