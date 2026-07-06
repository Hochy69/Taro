#!/bin/bash
set -euo pipefail
cd /opt/taro

echo "========== CELERY NOTIFICATIONS CHECK =========="

docker compose ps --format 'table {{.Name}}\t{{.Status}}' | grep -E 'celery|NAME' || true

echo ""
echo "--- Registered tasks ---"
docker compose exec -T celery_worker celery -A app.infrastructure.celery_app inspect registered 2>/dev/null | grep -E 'send_daily_card_push|check_subscription|check_inactive|send_start_no_webapp|send_compat_abandon|send_free_limit|send_compat_paid|send_weekly_referral' || {
  echo "FAIL: celery worker tasks not registered"
  exit 1
}

echo ""
echo "--- Recent notifications in DB ---"
docker compose exec -T backend python <<'PY'
import asyncio
from sqlalchemy import select, func
from app.infrastructure.database.models import Notification, User
from app.infrastructure.database.session import async_session

async def main():
    async with async_session() as session:
        total = (await session.execute(select(func.count(Notification.id)))).scalar_one()
        sent = (await session.execute(select(func.count(Notification.id)).where(Notification.is_sent == True))).scalar_one()
        eligible = (await session.execute(
            select(func.count(User.id)).where(User.is_blocked == False, User.daily_card_push == True)
        )).scalar_one()
        print(f"notifications total={total} sent={sent} eligible_push_users={eligible}")
        rows = (await session.execute(
            select(Notification).order_by(Notification.created_at.desc()).limit(5)
        )).scalars().all()
        for n in rows:
            print(f"  id={n.id} type={n.notification_type.value} sent={n.is_sent} at={n.created_at}")

asyncio.run(main())
PY

echo ""
echo "--- Trigger test daily card push ---"
docker compose exec -T celery_worker celery -A app.infrastructure.celery_app call app.infrastructure.tasks.send_daily_card_push

echo ""
echo "--- Worker logs (tail) ---"
docker compose logs celery_worker --tail 20
docker compose logs celery_beat --tail 10

echo "DONE"
