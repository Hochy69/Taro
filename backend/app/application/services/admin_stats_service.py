"""Admin dashboard statistics — production metrics exclude QA and admin accounts."""

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    AIResult,
    Payment,
    PaymentStatus,
    Spread,
    SpreadStatus,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    User,
)

MSK = ZoneInfo("Europe/Moscow")

# Internal / QA accounts that must not skew production metrics.
TEST_TELEGRAM_IDS: frozenset[int] = frozenset({
    0,  # dev browser user
    999999,  # limit-test script
    999888777,  # seed test user
    999999001,  # subscription payment integration tests
    555000111,  # manual admin API test
    555001,
    555002,
    900000001,  # remote admin panel health-check grant
})


def _msk_day_bounds(day) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=MSK)
    end = start + timedelta(days=1)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def _is_production_user():
    """Real end-users only — excludes QA accounts and internal admins."""
    return and_(
        User.telegram_id.notin_(TEST_TELEGRAM_IDS),
        User.is_admin.is_(False),
    )


def _is_real_payment():
    """Ignore synthetic QA / promo charges."""
    tid = Payment.telegram_payment_id
    return or_(
        tid.is_(None),
        and_(~tid.like("test_%"), ~tid.like("promo_%")),
    )


class AdminStatsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dashboard(self) -> dict:
        now = datetime.now(timezone.utc)
        today_msk = datetime.now(MSK).date()
        day_start, day_end = _msk_day_bounds(today_msk)
        month_ago = now - timedelta(days=30)
        prod = _is_production_user()

        total_users = (
            await self.session.execute(select(func.count(User.id)).where(prod))
        ).scalar() or 0

        dau = (
            await self.session.execute(
                select(func.count(User.id)).where(
                    prod,
                    User.last_active_at.is_not(None),
                    User.last_active_at >= day_start,
                    User.last_active_at < day_end,
                )
            )
        ).scalar() or 0

        mau = (
            await self.session.execute(
                select(func.count(User.id)).where(
                    prod,
                    User.last_active_at.is_not(None),
                    User.last_active_at >= month_ago,
                )
            )
        ).scalar() or 0

        new_users = (
            await self.session.execute(
                select(func.count(User.id)).where(
                    prod,
                    User.created_at >= day_start,
                    User.created_at < day_end,
                )
            )
        ).scalar() or 0

        # Paid/promo premium = valid subscription row (not stale is_premium / admin grant).
        active_premium_users = (
            await self.session.execute(
                select(func.count(func.distinct(Subscription.user_id)))
                .join(User, Subscription.user_id == User.id)
                .where(
                    prod,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.expires_at > now,
                    Subscription.plan != SubscriptionPlan.FREE,
                )
            )
        ).scalar() or 0

        paying_users = (
            await self.session.execute(
                select(func.count(func.distinct(Payment.user_id)))
                .join(User, Payment.user_id == User.id)
                .where(
                    prod,
                    Payment.status == PaymentStatus.COMPLETED,
                    _is_real_payment(),
                )
            )
        ).scalar() or 0

        total_revenue = (
            await self.session.execute(
                select(func.coalesce(func.sum(Payment.stars_amount), 0))
                .join(User, Payment.user_id == User.id)
                .where(
                    prod,
                    Payment.status == PaymentStatus.COMPLETED,
                    _is_real_payment(),
                )
            )
        ).scalar() or 0

        spreads_total = (
            await self.session.execute(
                select(func.count(Spread.id))
                .join(User, Spread.user_id == User.id)
                .where(prod)
            )
        ).scalar() or 0

        spreads_completed = (
            await self.session.execute(
                select(func.count(Spread.id))
                .join(User, Spread.user_id == User.id)
                .where(prod, Spread.status == SpreadStatus.COMPLETED)
            )
        ).scalar() or 0

        ai_generations = (
            await self.session.execute(
                select(func.count(AIResult.id))
                .join(Spread, AIResult.spread_id == Spread.id)
                .join(User, Spread.user_id == User.id)
                .where(prod)
            )
        ).scalar() or 0

        avg_ai_time = (
            await self.session.execute(
                select(func.avg(AIResult.generation_time_ms))
                .join(Spread, AIResult.spread_id == Spread.id)
                .join(User, Spread.user_id == User.id)
                .where(prod, AIResult.generation_time_ms > 0)
            )
        ).scalar() or 0

        conversion = (paying_users / total_users * 100) if total_users > 0 else 0
        arpu = (total_revenue / paying_users) if paying_users > 0 else 0

        return {
            "total_users": total_users,
            "dau": dau,
            "mau": mau,
            "new_registrations_today": new_users,
            "active_subscriptions": active_premium_users,
            "premium_users": active_premium_users,
            "paying_users": paying_users,
            "total_revenue_stars": int(total_revenue),
            "arpu": round(float(arpu), 2),
            "conversion_percent": round(conversion, 2),
            "total_spreads": spreads_total,
            "completed_spreads": spreads_completed,
            "ai_generations": ai_generations,
            "avg_ai_response_ms": round(float(avg_ai_time), 0),
        }
