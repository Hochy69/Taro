"""Promo codes for percentage discounts."""

from alembic import op
import sqlalchemy as sa

revision = "007_promo_codes"
down_revision = "006_astrology_phase2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "promo_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("discount_percent", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_promo_codes_code", "promo_codes", ["code"], unique=True)

    op.create_table(
        "promo_code_uses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("promo_code_id", sa.Integer(), sa.ForeignKey("promo_codes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("payments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "promo_code_id", name="uq_promo_user_code"),
    )
    op.create_index("ix_promo_code_uses_promo_code_id", "promo_code_uses", ["promo_code_id"])
    op.create_index("ix_promo_code_uses_user_id", "promo_code_uses", ["user_id"])

    op.add_column("payments", sa.Column("original_stars_amount", sa.Integer(), nullable=True))
    op.add_column("payments", sa.Column("promo_code_id", sa.Integer(), sa.ForeignKey("promo_codes.id", ondelete="SET NULL"), nullable=True))

    op.bulk_insert(
        sa.table(
            "promo_codes",
            sa.column("code", sa.String),
            sa.column("discount_percent", sa.Integer),
            sa.column("is_active", sa.Boolean),
            sa.column("max_uses", sa.Integer),
        ),
        [
            {"code": "TARO10", "discount_percent": 10, "max_uses": 5, "is_active": True},
            {"code": "TARO20", "discount_percent": 20, "max_uses": 5, "is_active": True},
            {"code": "TARO50", "discount_percent": 50, "max_uses": 5, "is_active": True},
            {"code": "TARO100", "discount_percent": 100, "max_uses": 5, "is_active": True},
        ],
    )


def downgrade() -> None:
    op.drop_column("payments", "promo_code_id")
    op.drop_column("payments", "original_stars_amount")
    op.drop_table("promo_code_uses")
    op.drop_table("promo_codes")
