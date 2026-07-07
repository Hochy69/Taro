import enum
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.session import Base


class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    MONTH_1 = "month_1"
    MONTH_3 = "month_3"
    MONTH_6 = "month_6"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PaymentType(str, enum.Enum):
    SINGLE_SPREAD = "single_spread"
    SUBSCRIPTION = "subscription"
    COMPATIBILITY = "compatibility"
    SPREAD_PACK_3 = "spread_pack_3"
    SPREAD_PACK_5 = "spread_pack_5"
    LOVE_BUNDLE = "love_bundle"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class SpreadStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class NotificationType(str, enum.Enum):
    SUBSCRIPTION_EXPIRING_3D = "subscription_expiring_3d"
    SUBSCRIPTION_EXPIRING_TODAY = "subscription_expiring_today"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    INACTIVE_3D = "inactive_3d"
    INACTIVE_7D = "inactive_7d"
    INACTIVE_14D = "inactive_14d"
    CARD_OF_DAY = "card_of_day"
    START_NO_WEBAPP = "start_no_webapp"
    SPREAD_FIRST = "spread_first"
    SPREAD_SECOND = "spread_second"
    SPREAD_THIRD = "spread_third"
    FREE_LIMIT_HIT = "free_limit_hit"
    FREE_LIMIT_FOLLOWUP = "free_limit_followup"
    COMPAT_VIEW_ABANDONED = "compat_view_abandoned"
    COMPAT_PAID_UPSELL = "compat_paid_upsell"
    WEEKLY_REFERRAL = "weekly_referral"


def _notification_type_enum():
    """PostgreSQL stores enum member names (CARD_OF_DAY), not .value strings."""
    return Enum(
        NotificationType,
        values_callable=lambda members: [m.name for m in members],
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    language_code: Mapped[str] = mapped_column(String(10), default="ru")
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    referral_code: Mapped[str | None] = mapped_column(String(16), unique=True, index=True)
    referred_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    terms_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    daily_card_push: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    profile: Mapped["Profile | None"] = relationship(back_populates="user", uselist=False)
    spreads: Mapped[list["Spread"]] = relationship(back_populates="user")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")
    payments: Mapped[list["Payment"]] = relationship(back_populates="user")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")
    limits: Mapped["UserLimit | None"] = relationship(back_populates="user", uselist=False)
    referrals_made: Mapped[list["Referral"]] = relationship(
        back_populates="referrer",
        foreign_keys="Referral.referrer_id",
    )


class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = (UniqueConstraint("referee_id", name="uq_referrals_referee_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referrer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    referee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    referrer: Mapped["User"] = relationship(back_populates="referrals_made", foreign_keys=[referrer_id])
    referee: Mapped["User"] = relationship(foreign_keys=[referee_id])


class ReferralPending(Base):
    __tablename__ = "referral_pending"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    referral_code: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str | None] = mapped_column(String(100))
    birth_date: Mapped[date | None] = mapped_column(Date)
    birth_time: Mapped[str | None] = mapped_column(String(8))
    birth_city: Mapped[str | None] = mapped_column(String(120))
    gender: Mapped[str | None] = mapped_column(String(1))
    zodiac_sign: Mapped[str | None] = mapped_column(String(50))
    lunar_birth_day: Mapped[int | None] = mapped_column(Integer)
    birth_lat: Mapped[float | None] = mapped_column(Float)
    birth_lon: Mapped[float | None] = mapped_column(Float)
    birth_timezone: Mapped[int | None] = mapped_column(Integer)
    last_category_slug: Mapped[str | None] = mapped_column(String(50))

    user: Mapped["User"] = relationship(back_populates="profile")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    emoji: Mapped[str] = mapped_column(String(10))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    spreads: Mapped[list["Spread"]] = relationship(back_populates="category")
    analytics: Mapped[list["AnalyticsEvent"]] = relationship(back_populates="category")


class TarotDeck(Base):
    __tablename__ = "tarot_decks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    cards: Mapped[list["TarotCard"]] = relationship(back_populates="deck")


class TarotCard(Base):
    __tablename__ = "tarot_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey("tarot_decks.id", ondelete="CASCADE"))
    slug: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(100))
    arcana: Mapped[str] = mapped_column(String(20))  # major / minor
    suit: Mapped[str | None] = mapped_column(String(20))
    number: Mapped[int | None] = mapped_column(Integer)
    image_url: Mapped[str | None] = mapped_column(String(500))

    deck: Mapped["TarotDeck"] = relationship(back_populates="cards")
    meanings: Mapped[list["TarotMeaning"]] = relationship(back_populates="card")
    spread_cards: Mapped[list["SpreadCard"]] = relationship(back_populates="card")


class TarotMeaning(Base):
    __tablename__ = "tarot_meanings"
    __table_args__ = (UniqueConstraint("card_id", "category_slug", "position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("tarot_cards.id", ondelete="CASCADE"))
    category_slug: Mapped[str] = mapped_column(String(50), default="general")
    position: Mapped[str] = mapped_column(String(20))  # past, present, future, upright, reversed
    keywords: Mapped[str | None] = mapped_column(String(500))
    meaning: Mapped[str] = mapped_column(Text)
    advice: Mapped[str | None] = mapped_column(Text)

    card: Mapped["TarotCard"] = relationship(back_populates="meanings")


class Spread(Base):
    __tablename__ = "spreads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    situation: Mapped[str | None] = mapped_column(Text)
    emotion: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[SpreadStatus] = mapped_column(Enum(SpreadStatus), default=SpreadStatus.PENDING)
    quota_from_bonus: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="spreads")
    category: Mapped["Category"] = relationship(back_populates="spreads")
    cards: Mapped[list["SpreadCard"]] = relationship(back_populates="spread", cascade="all, delete-orphan")
    ai_result: Mapped["AIResult | None"] = relationship(back_populates="spread", uselist=False)
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="spread")


class SpreadCard(Base):
    __tablename__ = "spread_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spread_id: Mapped[int] = mapped_column(ForeignKey("spreads.id", ondelete="CASCADE"))
    card_id: Mapped[int] = mapped_column(ForeignKey("tarot_cards.id"))
    position: Mapped[str] = mapped_column(String(20))  # past, present, future
    is_reversed: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer)

    spread: Mapped["Spread"] = relationship(back_populates="cards")
    card: Mapped["TarotCard"] = relationship(back_populates="spread_cards")


class AIResult(Base):
    __tablename__ = "ai_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spread_id: Mapped[int] = mapped_column(ForeignKey("spreads.id", ondelete="CASCADE"), unique=True)
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    generation_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    response_text: Mapped[str] = mapped_column(Text)
    past_interpretation: Mapped[str | None] = mapped_column(Text)
    present_interpretation: Mapped[str | None] = mapped_column(Text)
    future_interpretation: Mapped[str | None] = mapped_column(Text)
    advice: Mapped[str | None] = mapped_column(Text)
    conclusion: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    spread: Mapped["Spread"] = relationship(back_populates="ai_result")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan: Mapped[SubscriptionPlan] = mapped_column(Enum(SubscriptionPlan))
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    stars_amount: Mapped[int] = mapped_column(Integer)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="subscriptions")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    telegram_payment_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    payment_type: Mapped[PaymentType] = mapped_column(Enum(PaymentType))
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    stars_amount: Mapped[int] = mapped_column(Integer)
    original_stars_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    promo_code_id: Mapped[int | None] = mapped_column(
        ForeignKey("promo_codes.id", ondelete="SET NULL"), nullable=True
    )
    plan: Mapped[SubscriptionPlan | None] = mapped_column(Enum(SubscriptionPlan), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="payments")
    promo_code: Mapped["PromoCode | None"] = relationship(back_populates="payments")


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    discount_percent: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    uses: Mapped[list["PromoCodeUse"]] = relationship(back_populates="promo_code")
    payments: Mapped[list["Payment"]] = relationship(back_populates="promo_code")


class PromoCodeUse(Base):
    __tablename__ = "promo_code_uses"
    __table_args__ = (UniqueConstraint("user_id", "promo_code_id", name="uq_promo_user_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promo_code_id: Mapped[int] = mapped_column(ForeignKey("promo_codes.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    promo_code: Mapped["PromoCode"] = relationship(back_populates="uses")
    user: Mapped["User"] = relationship()
    payment: Mapped["Payment | None"] = relationship()


class UserLimit(Base):
    __tablename__ = "limits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    daily_spreads_used: Mapped[int] = mapped_column(Integer, default=0)
    bonus_spreads: Mapped[int] = mapped_column(Integer, default=0)
    compatibility_credits: Mapped[int] = mapped_column(Integer, default=0)
    last_reset_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())

    user: Mapped["User"] = relationship(back_populates="limits")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "spread_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    spread_id: Mapped[int] = mapped_column(ForeignKey("spreads.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="favorites")
    spread: Mapped["Spread"] = relationship(back_populates="favorites")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    notification_type: Mapped[NotificationType] = mapped_column(_notification_type_enum())
    message: Mapped[str] = mapped_column(Text)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="notifications")


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnalyticsEvent(Base):
    __tablename__ = "analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    metadata_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped["Category | None"] = relationship(back_populates="analytics")
