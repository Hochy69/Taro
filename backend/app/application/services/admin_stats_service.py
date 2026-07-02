"""Admin dashboard statistics — excludes test accounts and uses UTC day boundaries."""

from datetime import datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    AIResult,
    Payment,
    PaymentStatus,
    Spread,
    SpreadStatus,
    Subscription,
    SubscriptionStatus,
    User,
)

# Internal / QA accounts that must not skew production metrics.
TEST_TELEGRAM_IDS: frozenset[int] = frozenset({
    0,          # dev browser user
    999999,     # limit-test script
    999888777,  # seed test user
    555000111,  # manual test
    555001,
    555002,
})


def _utc_day_bounds(day: datetime.date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


def _real_users_filter():
    return User.telegram_id.notin_(TEST_TELEGRAM_IDS)


class AdminStatsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dashboard(self) -> dict:
        now = datetime.now(timezone.utc)
        today = now.date()
        day_start, day_end = _utc_day_bounds(today)
        month_ago = now - timedelta(days=30)

        real = _real_users_filter()

        total_users = (
            await self.session.execute(
                select(func.count(User.id)).where(real)
            )
        ).scalar() or 0

        dau = (
            await self.session.execute(
                select(func.count(User.id)).where(
                    real,
                    User.last_active_at >= day_start,
                    User.last_active_at < day_end,
                )
            )
        ).scalar() or 0

        mau = (
            await self.session.execute(
                select(func.count(User.id)).where(
                    real,
                    User.last_active_at >= month_ago,
                )
            )
        ).scalar() or 0

        new_users = (
            await self.session.execute(
                select(func.count(User.id)).where(
                    real,
                    User.created_at >= day_start,
                    User.created_at < day_end,
                )
            )
        ).scalar() or 0

        active_subs = (
            await self.session.execute(
                select(func.count(Subscription.id))
                .join(User, Subscription.user_id == User.id)
                .where(
                    real,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.expires_at > now,
                )
            )
        ).scalar() or 0

        premium_users = (
            await self.session.execute(
                select(func.count(User.id)).where(real, User.is_premium.is_(True))
            )
        ).scalar() or 0

        paying_users = (
            await self.session.execute(
                select(func.count(func.distinct(Payment.user_id)))
                .join(User, Payment.user_id == User.id)
                .where(real, Payment.status == PaymentStatus.COMPLETED)
            )
        ).scalar() or 0

        total_revenue = (
            await self.session.execute(
                select(func.coalesce(func.sum(Payment.stars_amount), 0))
                .join(User, Payment.user_id == User.id)
                .where(real, Payment.status == PaymentStatus.COMPLETED)
            )
        ).scalar() or 0

        spreads_total = (
            await self.session.execute(
                select(func.count(Spread.id))
                .join(User, Spread.user_id == User.id)
                .where(real)
            )
        ).scalar() or 0

        spreads_completed = (
            await self.session.execute(
                select(func.count(Spread.id))
                .join(User, Spread.user_id == User.id)
                .where(real, Spread.status == SpreadStatus.COMPLETED)
            )
        ).scalar() or 0

        ai_generations = (
            await self.session.execute(
                select(func.count(AIResult.id))
                .join(Spread, AIResult.spread_id == Spread.id)
                .join(User, Spread.user_id == User.id)
                .where(real)
            )
        ).scalar() or 0

        avg_ai_time = (
            await self.session.execute(
                select(func.avg(AIResult.generation_time_ms))
                .join(Spread, AIResult.spread_id == Spread.id)
                .join(User, Spread.user_id == User.id)
                .where(real)
            )
        ).scalar() or 0

        conversion = (paying_users / total_users * 100) if total_users > 0 else 0
        arpu = (total_revenue / total_users) if total_users > 0 else 0

        return {
            "total_users": total_users,
            "dau": dau,
            "mau": mau,
            "new_registrations_today": new_users,
            "active_subscriptions": active_subs,
            "premium_users": premium_users,
            "paying_users": paying_users,
            "total_revenue_stars": int(total_revenue),
            "arpu": round(float(arpu), 2),
            "conversion_percent": round(conversion, 2),
            "total_spreads": spreads_total,
            "completed_spreads": spreads_completed,
            "ai_generations": ai_generations,
            "avg_ai_response_ms": round(float(avg_ai_time), 0),
        }
