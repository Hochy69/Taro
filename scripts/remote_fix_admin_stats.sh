#!/bin/bash
set -euo pipefail
cd /opt/taro

# Files already uploaded by deploy script; just rebuild/restart and verify
docker compose build --no-cache backend frontend
docker compose up -d backend frontend
sleep 25

echo "--- pytest ---"
docker compose exec -T backend python -m pytest tests/test_admin_stats.py -q

echo ""
echo "--- dashboard after fix ---"
docker compose exec -T backend python <<'PY'
import asyncio
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select, func
from app.application.services.admin_stats_service import (
    AdminStatsService, TEST_TELEGRAM_IDS, _is_production_user, _is_real_payment, _msk_day_bounds
)
from app.infrastructure.database.models import User, Payment, PaymentStatus, Spread, SpreadStatus, Subscription, SubscriptionStatus, SubscriptionPlan
from app.infrastructure.database.session import async_session

MSK = ZoneInfo("Europe/Moscow")

async def main():
    now = datetime.now(timezone.utc)
    today = datetime.now(MSK).date()
    day_start, day_end = _msk_day_bounds(today)
    month_ago = now - timedelta(days=30)
    prod = _is_production_user()
    async with async_session() as session:
        dash = await AdminStatsService(session).get_dashboard()
        checks = {
            "total_users": (await session.execute(select(func.count(User.id)).where(prod))).scalar_one(),
            "dau": (await session.execute(select(func.count(User.id)).where(prod, User.last_active_at >= day_start, User.last_active_at < day_end))).scalar_one(),
            "mau": (await session.execute(select(func.count(User.id)).where(prod, User.last_active_at >= month_ago))).scalar_one(),
            "new_registrations_today": (await session.execute(select(func.count(User.id)).where(prod, User.created_at >= day_start, User.created_at < day_end))).scalar_one(),
            "premium_users": (await session.execute(select(func.count(func.distinct(Subscription.user_id))).join(User, Subscription.user_id == User.id).where(prod, Subscription.status == SubscriptionStatus.ACTIVE, Subscription.expires_at > now, Subscription.plan != SubscriptionPlan.FREE))).scalar_one(),
            "paying_users": (await session.execute(select(func.count(func.distinct(Payment.user_id))).join(User, Payment.user_id == User.id).where(prod, Payment.status == PaymentStatus.COMPLETED, _is_real_payment()))).scalar_one(),
            "total_revenue_stars": int((await session.execute(select(func.coalesce(func.sum(Payment.stars_amount), 0)).join(User, Payment.user_id == User.id).where(prod, Payment.status == PaymentStatus.COMPLETED, _is_real_payment()))).scalar_one()),
            "total_spreads": (await session.execute(select(func.count(Spread.id)).join(User, Spread.user_id == User.id).where(prod))).scalar_one(),
            "completed_spreads": (await session.execute(select(func.count(Spread.id)).join(User, Spread.user_id == User.id).where(prod, Spread.status == SpreadStatus.COMPLETED))).scalar_one(),
        }
        ok = True
        for k, expected in checks.items():
            got = dash[k]
            match = got == expected
            if not match:
                ok = False
            print(f"{k}: expected={expected} dashboard={got} {'OK' if match else 'FAIL'}")
        print("DASHBOARD:", dash)
        print("RESULT:", "ALL MATCH" if ok else "MISMATCH")
        if not ok:
            raise SystemExit(1)

asyncio.run(main())
PY

echo "DEPLOY+VERIFY OK"
