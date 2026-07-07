#!/bin/bash
set -euo pipefail
cd /opt/taro
SECRET=$(grep '^INTERNAL_API_SECRET=' .env | cut -d= -f2-)
FAIL=0

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; FAIL=1; }

echo "========== NOTIFICATION SYSTEM AUDIT =========="

echo ""
echo "--- 1. Docker services ---"
for svc in taro-backend-1 taro-celery_worker-1 taro-celery_beat-1 taro-bot-1; do
  if docker compose ps --status running --format '{{.Name}}' | grep -qx "$svc"; then
    pass "running $svc"
  else
    fail "not running $svc"
  fi
done

echo ""
echo "--- 2. PostgreSQL enum (UPPERCASE names required) ---"
docker compose exec -T backend python <<'PY'
import asyncio
from sqlalchemy import text
from app.infrastructure.database.session import engine

REQUIRED = [
    "CARD_OF_DAY",
    "START_NO_WEBAPP",
    "SPREAD_FIRST",
    "SPREAD_SECOND",
    "SPREAD_THIRD",
    "FREE_LIMIT_HIT",
    "FREE_LIMIT_FOLLOWUP",
    "COMPAT_VIEW_ABANDONED",
    "COMPAT_PAID_UPSELL",
    "WEEKLY_REFERRAL",
]

async def main():
    async with engine.connect() as conn:
        rows = (await conn.execute(text(
            "SELECT unnest(enum_range(NULL::notificationtype))::text"
        ))).scalars().all()
    missing = [v for v in REQUIRED if v not in rows]
    if missing:
        raise SystemExit(f"MISSING PG ENUM: {missing}")
    print("PG enum OK:", len(REQUIRED), "types present")

asyncio.run(main())
PY
pass "postgresql enum uppercase" || fail "postgresql enum uppercase"

echo ""
echo "--- 3. ORM insert/select all marketing notification types ---"
docker compose exec -T backend python <<'PY'
import asyncio
from datetime import datetime, timezone
from sqlalchemy import select, delete
from app.infrastructure.database.models import Notification, NotificationType, User
from app.infrastructure.database.session import async_session

MARKETING = [
    NotificationType.START_NO_WEBAPP,
    NotificationType.SPREAD_FIRST,
    NotificationType.SPREAD_SECOND,
    NotificationType.SPREAD_THIRD,
    NotificationType.FREE_LIMIT_HIT,
    NotificationType.FREE_LIMIT_FOLLOWUP,
    NotificationType.COMPAT_VIEW_ABANDONED,
    NotificationType.COMPAT_PAID_UPSELL,
    NotificationType.WEEKLY_REFERRAL,
]

async def main():
    async with async_session() as session:
        user = (await session.execute(select(User).limit(1))).scalar_one_or_none()
        if not user:
            raise SystemExit("no users in DB")
        created_ids = []
        for ntype in MARKETING:
            n = Notification(
                user_id=user.id,
                notification_type=ntype,
                message=f"audit test {ntype.name}",
                is_sent=False,
            )
            session.add(n)
            await session.flush()
            created_ids.append(n.id)
        await session.commit()

        async with async_session() as session2:
            for ntype in MARKETING:
                row = (await session2.execute(
                    select(Notification.id).where(
                        Notification.user_id == user.id,
                        Notification.notification_type == ntype,
                        Notification.message.like("audit test%"),
                    )
                )).scalar_one_or_none()
                if row is None:
                    raise SystemExit(f"roundtrip failed for {ntype.name}")
            await session2.execute(
                delete(Notification).where(Notification.id.in_(created_ids))
            )
            await session2.commit()
    print("ORM roundtrip OK for", len(MARKETING), "types")

asyncio.run(main())
PY
pass "orm notification roundtrip" || fail "orm notification roundtrip"

echo ""
echo "--- 4. Spread milestone push (celery task dry run) ---"
docker compose exec -T backend python <<'PY'
import asyncio
from sqlalchemy import select
from app.infrastructure.database.models import Spread, SpreadStatus, AIResult
from app.infrastructure.database.session import async_session
from app.application.services.marketing_push_service import on_spread_interpreted

async def main():
    async with async_session() as session:
        row = (await session.execute(
            select(Spread.id)
            .join(AIResult, AIResult.spread_id == Spread.id)
            .where(Spread.status == SpreadStatus.COMPLETED)
            .order_by(Spread.id.desc())
            .limit(1)
        )).scalar_one_or_none()
        if not row:
            print("skip: no completed spread with AI")
            return
        await on_spread_interpreted(session, row)
        await session.rollback()
    print("on_spread_interpreted OK (rolled back)")

asyncio.run(main())
PY
pass "spread milestone handler" || fail "spread milestone handler"

echo ""
echo "--- 5. Celery registered tasks ---"
docker compose exec -T celery_worker celery -A app.infrastructure.celery_app inspect registered 2>/dev/null | grep -E \
  'send_daily_card_push|check_subscription|check_inactive|send_start_no_webapp|send_compat_abandon|send_free_limit|send_compat_paid|send_weekly_referral|send_spread_milestone' \
  > /tmp/celery_tasks.txt
TASKS=$(wc -l < /tmp/celery_tasks.txt | tr -d ' ')
if [ "$TASKS" -ge 9 ]; then
  pass "celery tasks registered ($TASKS)"
  cat /tmp/celery_tasks.txt | sed 's/^/    /'
else
  fail "celery tasks registered ($TASKS/9)"
fi

echo ""
echo "--- 6. Internal APIs ---"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/notifications/bot-start \
  -H 'Content-Type: application/json' -d '{"telegram_id":1,"secret":"wrong"}')
[ "$CODE" = "403" ] && pass "bot-start rejects bad secret" || fail "bot-start bad secret -> $CODE"

curl -sf -X POST http://localhost:8000/api/v1/notifications/bot-start \
  -H 'Content-Type: application/json' \
  -d "{\"telegram_id\":888777666,\"secret\":\"${SECRET}\"}" \
  | python3 -c "import sys,json; assert json.load(sys.stdin).get('ok')" && pass "bot-start OK" || fail "bot-start"

echo ""
echo "--- 7. Unit tests ---"
docker compose exec -T backend python -m pytest tests/test_marketing_pushes.py -q && pass "pytest marketing" || fail "pytest marketing"

echo ""
echo "--- 8. Trigger daily card push (smoke) ---"
docker compose exec -T celery_worker celery -A app.infrastructure.celery_app call app.infrastructure.tasks.send_daily_card_push
sleep 3
docker compose logs celery_worker --tail 8 | grep -E 'Daily card push|ERROR|Traceback' || true
pass "daily card push invoked"

echo ""
echo "--- 9. Recent notification stats ---"
docker compose exec -T backend python <<'PY'
import asyncio
from sqlalchemy import select, func
from app.infrastructure.database.models import Notification, NotificationType
from app.infrastructure.database.session import async_session

async def main():
    async with async_session() as session:
        total = (await session.execute(select(func.count(Notification.id)))).scalar_one()
        sent = (await session.execute(
            select(func.count(Notification.id)).where(Notification.is_sent == True)
        )).scalar_one()
        print(f"total={total} sent={sent}")
        for ntype in NotificationType:
            c = (await session.execute(
                select(func.count(Notification.id)).where(
                    Notification.notification_type == ntype
                )
            )).scalar_one()
            if c:
                print(f"  {ntype.name}: {c}")

asyncio.run(main())
PY

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "========== NOTIFICATION AUDIT PASSED =========="
else
  echo "========== NOTIFICATION AUDIT FAILED =========="
  exit 1
fi
