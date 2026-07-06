from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.application.services.referral_service import grant_bonus_spreads, grant_compatibility_credit
from app.infrastructure.database.models import (
    Payment,
    PaymentStatus,
    PaymentType,
    PromoCode,
    PromoCodeUse,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    User,
)


PLAN_DURATIONS = {
    SubscriptionPlan.MONTH_1: 30,
    SubscriptionPlan.MONTH_3: 90,
    SubscriptionPlan.MONTH_6: 180,
}

PLAN_PRICES = {
    SubscriptionPlan.MONTH_1: settings.price_subscription_1m,
    SubscriptionPlan.MONTH_3: settings.price_subscription_3m,
    SubscriptionPlan.MONTH_6: settings.price_subscription_6m,
}


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def get_subscription_price(self, plan: SubscriptionPlan) -> int:
        return PLAN_PRICES.get(plan, 0)

    def get_single_spread_price(self) -> int:
        return settings.price_single_spread

    def get_compatibility_price(self) -> int:
        return settings.price_compatibility

    def get_spread_pack_price(self, pack: str) -> int:
        if pack == "spread_pack_3":
            return settings.price_spread_pack_3
        if pack == "spread_pack_5":
            return settings.price_spread_pack_5
        return 0

    def get_love_bundle_price(self) -> int:
        from app.application.services.marketing_service import love_bundle_price

        return love_bundle_price()

    async def create_payment(
        self,
        user: User,
        payment_type: PaymentType,
        stars_amount: int,
        plan: SubscriptionPlan | None = None,
        original_stars_amount: int | None = None,
        promo_code_id: int | None = None,
    ) -> Payment:
        payment = Payment(
            user_id=user.id,
            payment_type=payment_type,
            stars_amount=stars_amount,
            original_stars_amount=original_stars_amount,
            promo_code_id=promo_code_id,
            plan=plan,
            status=PaymentStatus.PENDING,
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def complete_free_payment(self, payment: Payment, promo: PromoCode) -> Payment:
        """100% promo — grant access without Telegram invoice."""
        if payment.status == PaymentStatus.COMPLETED:
            return payment
        payment.telegram_payment_id = f"promo_{promo.code}_{payment.id}"
        payment.status = PaymentStatus.COMPLETED
        await self._apply_purchase(payment)
        from app.application.services.promo_service import PromoService

        await PromoService(self.session).record_redemption(promo, payment.user_id, payment)
        await self.session.flush()
        return payment

    async def create_invoice_link(
        self, title: str, description: str, payload: str, stars: int
    ) -> str:
        """Create a Telegram Stars (XTR) invoice link via the Bot API."""
        import httpx

        token = settings.telegram_bot_token
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/createInvoiceLink",
                json={
                    "title": title,
                    "description": description,
                    "payload": payload,
                    "currency": "XTR",
                    "prices": [{"label": title, "amount": stars}],
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                raise ValueError(f"createInvoiceLink failed: {data}")
            return data["result"]

    async def _apply_purchase(self, payment: Payment) -> None:
        """Grant whatever the completed payment entitles the user to."""
        if payment.payment_type == PaymentType.SINGLE_SPREAD:
            await grant_bonus_spreads(self.session, payment.user_id, 1)
        elif payment.payment_type == PaymentType.SPREAD_PACK_3:
            await grant_bonus_spreads(self.session, payment.user_id, 3)
        elif payment.payment_type == PaymentType.SPREAD_PACK_5:
            await grant_bonus_spreads(self.session, payment.user_id, 5)
        elif payment.payment_type == PaymentType.COMPATIBILITY:
            await grant_compatibility_credit(self.session, payment.user_id, 1)
        elif payment.payment_type == PaymentType.LOVE_BUNDLE:
            await grant_compatibility_credit(self.session, payment.user_id, 1)
            await grant_bonus_spreads(self.session, payment.user_id, 1)
        elif payment.payment_type == PaymentType.SUBSCRIPTION and payment.plan:
            await self._activate_subscription(
                payment.user_id, payment.plan, payment.stars_amount
            )

    async def confirm_payment_by_id(
        self, payment_id: int, telegram_payment_charge_id: str
    ) -> Payment | None:
        """Confirm a specific payment (called from the bot after successful Stars payment)."""
        result = await self.session.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()
        if not payment:
            return None

        # Idempotent: if already completed, do nothing more.
        if payment.status == PaymentStatus.COMPLETED:
            return payment

        payment.telegram_payment_id = telegram_payment_charge_id
        payment.status = PaymentStatus.COMPLETED
        await self._apply_purchase(payment)
        if payment.promo_code_id:
            await self._record_promo_redemption(payment)
        await self.session.flush()
        return payment

    async def _record_promo_redemption(self, payment: Payment) -> None:
        existing = await self.session.execute(
            select(PromoCodeUse.id).where(PromoCodeUse.payment_id == payment.id)
        )
        if existing.scalar_one_or_none() is not None:
            return
        promo_result = await self.session.execute(
            select(PromoCode).where(PromoCode.id == payment.promo_code_id)
        )
        promo = promo_result.scalar_one_or_none()
        if not promo:
            return
        from app.application.services.promo_service import PromoService

        await PromoService(self.session).record_redemption(promo, payment.user_id, payment)

    async def confirm_payment(self, telegram_payment_id: str, user_id: int) -> Payment | None:
        result = await self.session.execute(
            select(Payment).where(
                Payment.user_id == user_id,
                Payment.telegram_payment_id == telegram_payment_id,
            )
        )
        payment = result.scalar_one_or_none()
        if payment:
            return payment

        try:
            payment_id = int(telegram_payment_id)
        except (TypeError, ValueError):
            return None

        result = await self.session.execute(
            select(Payment).where(
                Payment.user_id == user_id,
                Payment.status == PaymentStatus.PENDING,
                Payment.id == payment_id,
            )
        )
        payment = result.scalar_one_or_none()
        if not payment:
            return None

        payment.telegram_payment_id = telegram_payment_id
        payment.status = PaymentStatus.COMPLETED
        await self._apply_purchase(payment)
        await self.session.flush()
        return payment

    async def _activate_subscription(
        self, user_id: int, plan: SubscriptionPlan, stars_amount: int
    ) -> Subscription:
        now = datetime.now(timezone.utc)
        days = PLAN_DURATIONS.get(plan, 30)

        result = await self.session.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        )
        active_subs = list(result.scalars().all())
        current = None
        for sub in active_subs:
            if sub.expires_at > now:
                if current is None or sub.expires_at > current.expires_at:
                    current = sub
            else:
                sub.status = SubscriptionStatus.EXPIRED

        if current:
            current.plan = plan
            current.expires_at = current.expires_at + timedelta(days=days)
            current.stars_amount = stars_amount
            sub = current
        else:
            sub = Subscription(
                user_id=user_id,
                plan=plan,
                status=SubscriptionStatus.ACTIVE,
                stars_amount=stars_amount,
                starts_at=now,
                expires_at=now + timedelta(days=days),
            )
            self.session.add(sub)

        user_result = await self.session.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()
        user.is_premium = True
        await self.session.flush()
        return sub

    async def get_active_subscription(self, user_id: int) -> Subscription | None:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.expires_at > now,
                Subscription.plan != SubscriptionPlan.FREE,
            )
            .order_by(Subscription.expires_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
