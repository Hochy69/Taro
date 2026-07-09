#!/bin/bash
set -euo pipefail
cd /opt/taro

echo "========== ADMIN STATS AUDIT =========="

docker compose exec -T backend python <<'PY'
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_, or_

from app.application.services.admin_stats_service import (
    AdminStatsService,
    TEST_TELEGRAM_IDS,
    _is_production_user,
    _is_real_payment,
)
from app.infrastructure.database.models import (
    User, Payment, PaymentStatus, Spread, SpreadStatus, Subscription, SubscriptionStatus, AIResult
)
from app.infrastructure.database.session import async_session

async def main():
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    month_ago = now - timedelta(days=30)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    async with async_session() as session:
        dash = await AdminStatsService(session).get_dashboard()

        # RAW totals (including test users)
        raw_users = (await session.execute(select(func.count(User.id)))).scalar_one()
        raw_premium = (await session.execute(select(func.count(User.id)).where(User.is_premium == True))).scalar_one()
        raw_admins = (await session.execute(select(func.count(User.id)).where(User.is_admin == True))).scalar_one()
        raw_blocked = (await session.execute(select(func.count(User.id)).where(User.is_blocked == True))).scalar_one()
        raw_spreads = (await session.execute(select(func.count(Spread.id)))).scalar_one()
        raw_completed = (await session.execute(select(func.count(Spread.id)).where(Spread.status == SpreadStatus.COMPLETED))).scalar_one()
        raw_payments_all = (await session.execute(select(func.count(Payment.id)))).scalar_one()
        raw_payments_completed = (await session.execute(
            select(func.count(Payment.id)).where(Payment.status == PaymentStatus.COMPLETED)
        )).scalar_one()
        raw_revenue_all = (await session.execute(
            select(func.coalesce(func.sum(Payment.stars_amount), 0)).where(Payment.status == PaymentStatus.COMPLETED)
        )).scalar_one()

        # Production filters (same as dashboard)
        prod = _is_production_user()
        prod_users = (await session.execute(select(func.count(User.id)).where(prod))).scalar_one()
        prod_premium = (await session.execute(select(func.count(User.id)).where(prod, User.is_premium == True))).scalar_one()
        prod_dau = (await session.execute(
            select(func.count(User.id)).where(prod, User.last_active_at >= day_ago)
        )).scalar_one()
        prod_mau = (await session.execute(
            select(func.count(User.id)).where(prod, User.last_active_at >= month_ago)
        )).scalar_one()
        prod_new_today = (await session.execute(
            select(func.count(User.id)).where(prod, User.created_at >= today_start)
        )).scalar_one()
        prod_spreads = (await session.execute(
            select(func.count(Spread.id)).select_from(Spread).join(User, Spread.user_id == User.id).where(prod)
        )).scalar_one()
        prod_completed = (await session.execute(
            select(func.count(Spread.id)).select_from(Spread).join(User, Spread.user_id == User.id).where(
                prod, Spread.status == SpreadStatus.COMPLETED
            )
        )).scalar_one()
        prod_paying = (await session.execute(
            select(func.count(func.distinct(Payment.user_id)))
            .select_from(Payment).join(User, Payment.user_id == User.id)
            .where(prod, Payment.status == PaymentStatus.COMPLETED, _is_real_payment())
        )).scalar_one()
        prod_revenue = (await session.execute(
            select(func.coalesce(func.sum(Payment.stars_amount), 0))
            .select_from(Payment).join(User, Payment.user_id == User.id)
            .where(prod, Payment.status == PaymentStatus.COMPLETED, _is_real_payment())
        )).scalar_one()
        active_subs = (await session.execute(
            select(func.count(Subscription.id))
            .select_from(Subscription).join(User, Subscription.user_id == User.id)
            .where(prod, Subscription.status == SubscriptionStatus.ACTIVE, Subscription.expires_at > now)
        )).scalar_one()

        # List all users for transparency
        users = (await session.execute(select(User).order_by(User.id))).scalars().all()
        print("=== ALL USERS ===")
        for u in users:
            is_test = u.telegram_id in TEST_TELEGRAM_IDS or (u.username or "").lower().startswith("test") or (u.first_name or "").lower().startswith("test")
            print(
                f"id={u.id} tg={u.telegram_id} @{u.username} name={u.first_name!r} "
                f"premium={u.is_premium} admin={u.is_admin} blocked={u.is_blocked} "
                f"test={is_test} last_active={u.last_active_at} created={u.created_at}"
            )

        print("\n=== PAYMENTS ===")
        pays = (await session.execute(select(Payment).order_by(Payment.id.desc()).limit(20))).scalars().all()
        if not pays:
            print("(none)")
        for p in pays:
            print(
                f"id={p.id} user={p.user_id} type={p.payment_type} status={p.status} "
                f"stars={p.stars_amount} tid={p.telegram_payment_id!r} created={p.created_at}"
            )

        print("\n=== SUBSCRIPTIONS ===")
        subs = (await session.execute(select(Subscription).order_by(Subscription.id.desc()).limit(20))).scalars().all()
        if not subs:
            print("(none)")
        for s in subs:
            print(
                f"id={s.id} user={s.user_id} plan={s.plan} status={s.status} "
                f"expires={s.expires_at} created={s.created_at}"
            )

        print("\n=== RAW vs FILTERED vs DASHBOARD ===")
        rows = [
            ("total_users", raw_users, prod_users, dash["total_users"]),
            ("premium_users", raw_premium, prod_premium, dash["premium_users"]),
            ("dau", None, prod_dau, dash["dau"]),
            ("mau", None, prod_mau, dash["mau"]),
            ("new_today", None, prod_new_today, dash["new_registrations_today"]),
            ("active_subscriptions", None, active_subs, dash["active_subscriptions"]),
            ("paying_users", None, prod_paying, dash["paying_users"]),
            ("total_revenue_stars", int(raw_revenue_all), int(prod_revenue), dash["total_revenue_stars"]),
            ("total_spreads", raw_spreads, prod_spreads, dash["total_spreads"]),
            ("completed_spreads", raw_completed, prod_completed, dash["completed_spreads"]),
        ]
        ok = True
        for name, raw, filtered, dash_v in rows:
            match = filtered == dash_v
            if not match:
                ok = False
            print(f"{name}: raw={raw} filtered={filtered} dashboard={dash_v} {'OK' if match else 'MISMATCH'}")

        print("\n=== EXTRA RAW ===")
        print(f"admins={raw_admins} blocked={raw_blocked} payments_all={raw_payments_all} payments_completed={raw_payments_completed}")
        print(f"TEST_TELEGRAM_IDS={sorted(TEST_TELEGRAM_IDS)}")
        print(f"dashboard_full={dash}")
        print("\nRESULT:", "STATS MATCH FILTERED COUNTS" if ok else "STATS MISMATCH")

asyncio.run(main())
PY
