"""Marketing eligibility: first-purchase discount, bundle pricing."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.promo_service import discounted_price
from app.core.config import settings
from app.infrastructure.database.models import (
    Payment,
    PaymentStatus,
    PaymentType,
    Spread,
    SpreadStatus,
)


async def count_completed_spreads(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(Spread)
        .where(Spread.user_id == user_id, Spread.status == SpreadStatus.COMPLETED)
    )
    return int(result.scalar_one() or 0)


async def has_completed_single_spread_payment(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(
        select(Payment.id)
        .where(
            Payment.user_id == user_id,
            Payment.payment_type == PaymentType.SINGLE_SPREAD,
            Payment.status == PaymentStatus.COMPLETED,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def is_first_paid_discount_eligible(session: AsyncSession, user_id: int) -> bool:
    """True after free tier spreads are used and before the first paid single spread."""
    if await has_completed_single_spread_payment(session, user_id):
        return False
    return await count_completed_spreads(session, user_id) >= settings.free_spreads_per_period


def first_paid_discounted_price() -> int:
    return discounted_price(
        settings.price_single_spread,
        settings.first_paid_discount_percent,
    )


def love_bundle_base_price() -> int:
    return settings.price_compatibility + settings.price_single_spread


def love_bundle_price() -> int:
    return discounted_price(love_bundle_base_price(), settings.love_bundle_discount_percent)


def love_bundle_effective_discount(promo_percent: int | None) -> int:
    """Bundle sale and promo stack by best discount, never worse than bundle price."""
    bundle_percent = settings.love_bundle_discount_percent
    if promo_percent and promo_percent > 0:
        return max(promo_percent, bundle_percent)
    return bundle_percent


def spread_pack_savings_percent(pack_stars: int, spreads: int) -> int:
    single_total = settings.price_single_spread * spreads
    if single_total <= 0:
        return 0
    return max(0, round((1 - pack_stars / single_total) * 100))
