"""Add referral system: codes, referrals audit, pending deep links."""

from alembic import op
import sqlalchemy as sa

revision = "004_add_referrals"
down_revision = "003_add_is_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("referral_code", sa.String(16), nullable=True))
    op.add_column("users", sa.Column("referred_by_id", sa.Integer(), nullable=True))
    op.create_index("ix_users_referral_code", "users", ["referral_code"], unique=True)
    op.create_foreign_key(
        "fk_users_referred_by_id",
        "users",
        "users",
        ["referred_by_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("referrer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referee_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("referee_id", name="uq_referrals_referee_id"),
    )
    op.create_index("ix_referrals_referrer_id", "referrals", ["referrer_id"])

    op.create_table(
        "referral_pending",
        sa.Column("telegram_id", sa.BigInteger(), primary_key=True),
        sa.Column("referral_code", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("referral_pending")
    op.drop_table("referrals")
    op.drop_constraint("fk_users_referred_by_id", "users", type_="foreignkey")
    op.drop_index("ix_users_referral_code", table_name="users")
    op.drop_column("users", "referred_by_id")
    op.drop_column("users", "referral_code")
