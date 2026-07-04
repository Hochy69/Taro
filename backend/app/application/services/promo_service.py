"""Promo codes with percentage discounts on paid features."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Payment, PromoCode, PromoCodeUse

DEFAULT_PROMO_CODES: list[tuple[str, int, int]] = [
    ("TARO10", 10, 5),
    ("TARO20", 20, 5),
    ("TARO50", 50, 5),
    ("TARO100", 100, 5),
]


def discounted_price(base_price: int, discount_percent: int) -> int:
    if discount_percent >= 100:
        return 0
    if discount_percent <= 0:
        return base_price
    return max(1, round(base_price * (100 - discount_percent) / 100))


class PromoService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ensure_default_codes(self) -> None:
        for code, percent, max_uses in DEFAULT_PROMO_CODES:
            result = await self.session.execute(
                select(PromoCode).where(PromoCode.code == code)
            )
            promo = result.scalar_one_or_none()
            if promo is None:
                self.session.add(
                    PromoCode(
                        code=code,
                        discount_percent=percent,
                        max_uses=max_uses,
                        is_active=True,
                    )
                )
            else:
                promo.discount_percent = percent
                promo.max_uses = max_uses
                promo.is_active = True
        await self.session.flush()

    async def validate_for_user(self, code: str, user_id: int) -> PromoCode:
        normalized = code.strip().upper()
        if not normalized:
            raise ValueError("Введите промокод")

        result = await self.session.execute(
            select(PromoCode).where(PromoCode.code == normalized)
        )
        promo = result.scalar_one_or_none()
        if not promo or not promo.is_active:
            raise ValueError("Промокод не найден или неактивен")

        if promo.max_uses is not None and promo.used_count >= promo.max_uses:
            raise ValueError("Промокод исчерпан")

        used = await self.session.execute(
            select(PromoCodeUse.id).where(
                PromoCodeUse.promo_code_id == promo.id,
                PromoCodeUse.user_id == user_id,
            )
        )
        if used.scalar_one_or_none() is not None:
            raise ValueError("Вы уже использовали этот промокод")

        return promo

    async def record_redemption(
        self, promo: PromoCode, user_id: int, payment: Payment
    ) -> None:
        self.session.add(
            PromoCodeUse(
                promo_code_id=promo.id,
                user_id=user_id,
                payment_id=payment.id,
            )
        )
        promo.used_count += 1
        await self.session.flush()
