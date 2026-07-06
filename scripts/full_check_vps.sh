#!/bin/bash
set -euo pipefail
cd /opt/taro
SECRET=$(grep '^INTERNAL_API_SECRET=' .env | cut -d= -f2-)
BOT_TOKEN=$(grep '^TELEGRAM_BOT_TOKEN=' .env | cut -d= -f2-)
FAIL=0

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; FAIL=1; }

echo "========== 1. DOCKER SERVICES =========="
docker compose ps --format 'table {{.Name}}\t{{.Status}}' | tee /tmp/taro_ps.txt
for svc in taro-backend-1 taro-frontend-1 taro-bot-1 taro-postgres-1 taro-redis-1 taro-celery_worker-1 taro-celery_beat-1; do
  if docker compose ps --status running --format '{{.Name}}' | grep -qx "$svc"; then
    pass "container $svc running"
  else
    fail "container $svc not running"
  fi
done

echo ""
echo "========== 2. HEALTH & PUBLIC URLS =========="
curl -sf http://localhost:8000/health | grep -q '"status":"ok"' && pass "backend /health" || fail "backend /health"
curl -sf -o /dev/null -w "%{http_code}" http://localhost:5173/ | grep -q 200 && pass "frontend :5173" || fail "frontend :5173"
CODE=$(curl -sf -o /dev/null -w "%{http_code}" https://91-184-249-229.sslip.io/)
[ "$CODE" = "200" ] && pass "public HTTPS $CODE" || fail "public HTTPS $CODE"

echo ""
echo "========== 3. PYTEST (ALL) =========="
docker compose exec -T backend python -m pytest tests/ -q --tb=short || fail "pytest"

echo ""
echo "========== 4. PRICING & PLANS =========="
python3 <<'PY'
import json, urllib.request, sys
with urllib.request.urlopen('http://localhost:8000/api/v1/pricing') as r:
    p = json.load(r)
plans = {x['plan']: x for x in p['plans']}
expected = {
    'month_1': (399, 30),
    'month_3': (999, 90),
    'month_6': (1799, 180),
}
for plan, (stars, days) in expected.items():
    got = plans[plan]
    assert got['stars'] == stars and got['duration_days'] == days, (plan, got)
assert p['single_spread'] == 59
assert p['compatibility'] == 79
print('pricing OK', list(expected.keys()))
PY
pass "pricing API all plans"

echo ""
echo "========== 5. PAYMENT PRE-CHECKOUT =========="
CODE=$(curl -s -o /tmp/precheck_bad.json -w "%{http_code}" -X POST http://localhost:8000/api/v1/payments/telegram/pre-checkout \
  -H 'Content-Type: application/json' \
  -d "{\"secret\":\"wrong\",\"payload\":\"1\",\"total_amount\":450,\"currency\":\"XTR\"}")
[ "$CODE" = "403" ] && pass "pre-checkout bad secret -> 403" || fail "pre-checkout bad secret -> $CODE"

curl -sf -X POST http://localhost:8000/api/v1/payments/telegram/pre-checkout \
  -H 'Content-Type: application/json' \
  -d "{\"secret\":\"${SECRET}\",\"payload\":\"99999999\",\"total_amount\":450,\"currency\":\"XTR\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('ok') is False" && pass "pre-checkout missing payment rejected" || fail "pre-checkout missing payment"

echo ""
echo "========== 6. SUBSCRIPTION ACTIVATION (DB SIM) =========="
docker compose exec -T backend python <<'PY'
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.services.payment_service import PaymentService, PLAN_DURATIONS, PLAN_PRICES
from app.infrastructure.database.models import (
    Payment, PaymentStatus, PaymentType, Subscription, SubscriptionPlan,
    SubscriptionStatus, User,
)

async def main():
    import time
    from app.core.config import settings
    run_id = int(time.time())
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        svc = PaymentService(db)
        uid = 999999001
        user = (await db.execute(select(User).where(User.telegram_id == uid))).scalar_one_or_none()
        if user:
            for model in (Payment, Subscription):
                rows = (await db.execute(select(model).where(model.user_id == user.id))).scalars().all()
                for row in rows:
                    await db.delete(row)
            await db.flush()
        else:
            user = User(telegram_id=uid, first_name='Test', terms_accepted_at=datetime.now(timezone.utc))
            db.add(user)
            await db.flush()

        for plan in (SubscriptionPlan.MONTH_1, SubscriptionPlan.MONTH_3, SubscriptionPlan.MONTH_6):
            pay = await svc.create_payment(user, PaymentType.SUBSCRIPTION, PLAN_PRICES[plan], plan)
            await svc.confirm_payment_by_id(pay.id, f'test_charge_{plan.value}_{run_id}')
            sub = await svc.get_active_subscription(user.id)
            assert sub and sub.plan == plan, plan
            days = PLAN_DURATIONS[plan]
            assert (sub.expires_at - datetime.now(timezone.utc)).days >= days - 1, plan
        pay2 = await svc.create_payment(user, PaymentType.SUBSCRIPTION, PLAN_PRICES[SubscriptionPlan.MONTH_1], SubscriptionPlan.MONTH_1)
        before = (await svc.get_active_subscription(user.id)).expires_at
        await svc.confirm_payment_by_id(pay2.id, f'test_stack_{run_id}')
        after = (await svc.get_active_subscription(user.id)).expires_at
        assert after > before
        print('subscription activation OK for month_1/3/6 + stack')
        await db.commit()
    await engine.dispose()

asyncio.run(main())
PY
pass "subscription DB simulation" || fail "subscription DB simulation"

echo ""
echo "========== 7. BOT API & WEBAPP URL =========="
curl -sf "https://api.telegram.org/bot${BOT_TOKEN}/getMe" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['ok']; print('bot:', d['result']['username'])" && pass "telegram bot getMe" || fail "telegram bot getMe"
WEBAPP=$(grep '^TELEGRAM_WEBAPP_URL=' .env | cut -d= -f2-)
curl -sf -o /dev/null -w "%{http_code}" "$WEBAPP/" | grep -q 200 && pass "webapp URL reachable" || fail "webapp URL"

echo ""
echo "========== 8. BOT -> BACKEND INTERNAL =========="
docker compose exec -T bot python -c "
import httpx, os
base=os.getenv('API_URL','http://backend:8000').rstrip('/')
secret=os.getenv('INTERNAL_API_SECRET','')
r=httpx.get(base+'/health',timeout=5); assert r.status_code==200
r=httpx.post(base+'/api/v1/payments/telegram/pre-checkout',json={'secret':secret,'payload':'1','total_amount':1,'currency':'XTR'},timeout=5)
assert r.status_code==200
print('bot internal API OK')
" && pass "bot internal API" || fail "bot internal API"

echo ""
echo "========== 9. ADMIN GRANT ENDPOINT =========="
CODE=$(curl -s -o /tmp/admin_bad.json -w "%{http_code}" -X POST http://localhost:8000/api/v1/admin/grant \
  -H 'Content-Type: application/json' \
  -d "{\"internal_secret\":\"wrong\",\"telegram_id\":1,\"word\":\"x\"}")
[ "$CODE" = "403" ] && pass "admin grant bad secret -> 403" || fail "admin grant -> $CODE"

echo ""
echo "========== 10. TELEGRAM INVOICE LINKS (all plans) =========="
docker compose exec -T backend python <<'PY'
import asyncio
from app.application.services.payment_service import PaymentService, PLAN_PRICES
from app.infrastructure.database.models import SubscriptionPlan

async def main():
    svc = PaymentService(None)  # only uses httpx + settings
    titles = {
        SubscriptionPlan.MONTH_1: "Подписка — 1 месяц",
        SubscriptionPlan.MONTH_3: "Подписка — 3 месяца",
        SubscriptionPlan.MONTH_6: "Подписка — 6 месяцев",
    }
    for plan in (SubscriptionPlan.MONTH_1, SubscriptionPlan.MONTH_3, SubscriptionPlan.MONTH_6):
        stars = PLAN_PRICES[plan]
        link = await svc.create_invoice_link(titles[plan], "Premium test", f"test_{plan.value}", stars)
        assert link.startswith("https://"), link
        print(plan.value, stars, "OK")
asyncio.run(main())
PY
pass "telegram invoice links month_1/3/6" || fail "invoice links"

echo ""
echo "========== 11. GIT VERSION =========="
git log -1 --oneline
pass "deployed commit"

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "========== ALL CHECKS PASSED =========="
else
  echo "========== SOME CHECKS FAILED =========="
  exit 1
fi
