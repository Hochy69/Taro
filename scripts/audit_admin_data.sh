#!/bin/bash
set -euo pipefail
cd /opt/taro
docker compose exec -T backend python <<'PY'
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings
from app.application.services.admin_stats_service import AdminStatsService, TEST_TELEGRAM_IDS
from app.infrastructure.database.models import (
    User, Payment, PaymentStatus, Subscription, SubscriptionStatus, Spread, SubscriptionPlan,
)

async def main():
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        print("=== USERS ===")
        users = (await db.execute(select(User).order_by(User.id))).scalars().all()
        for u in users:
            print(u.id, u.telegram_id, u.first_name, u.username, f"premium={u.is_premium}", f"admin={u.is_admin}", f"active={u.last_active_at}")

        print("\n=== PAYMENTS completed ===")
        pays = (await db.execute(
            select(Payment, User.telegram_id, User.first_name)
            .join(User, Payment.user_id == User.id)
            .where(Payment.status == PaymentStatus.COMPLETED)
            .order_by(Payment.id)
        )).all()
        total = 0
        for p, tg, name in pays:
            test = tg in TEST_TELEGRAM_IDS
            total += p.stars_amount
            print(p.id, tg, name, p.payment_type.value, p.plan, p.stars_amount, "TEST" if test else "real")

        print("sum all payments:", total)
        real_sum = sum(p.stars_amount for p, tg, _ in pays if tg not in TEST_TELEGRAM_IDS)
        print("sum real users:", real_sum)

        print("\n=== SUBSCRIPTIONS active ===")
        now = datetime.now(timezone.utc)
        subs = (await db.execute(
            select(Subscription, User.telegram_id)
            .join(User, Subscription.user_id == User.id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
        )).all()
        for s, tg in subs:
            valid = s.expires_at > now
            print(s.id, tg, s.plan.value, s.expires_at, "valid" if valid else "EXPIRED")

        dash = await AdminStatsService(db).get_dashboard()
        print("\n=== DASHBOARD ===")
        for k, v in dash.items():
            print(k, v)

    await engine.dispose()

asyncio.run(main())
PY
