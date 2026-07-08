#!/bin/bash
set -euo pipefail
cd /opt/taro

echo "========== DAILY PUSH DIAGNOSTIC $(date -Iseconds) =========="

echo ""
echo "--- Docker celery services ---"
docker compose ps --format 'table {{.Name}}\t{{.Status}}' | grep -E 'celery|NAME' || true

echo ""
echo "--- Beat logs (today, daily card) ---"
docker compose logs celery_beat --since 24h 2>&1 | grep -iE 'daily|card|beat|Scheduler|send-daily|error|traceback' | tail -40 || true

echo ""
echo "--- Worker logs (today, daily card) ---"
docker compose logs celery_worker --since 24h 2>&1 | grep -iE 'Daily card|send_daily_card|ERROR|Traceback|CARD_OF_DAY' | tail -40 || true

echo ""
echo "--- DB: CARD_OF_DAY notifications today (MSK) ---"
docker compose exec -T backend python <<'PY'
import asyncio
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select, func

from app.infrastructure.database.models import Notification, NotificationType, User
from app.infrastructure.database.session import async_session

MSK = ZoneInfo("Europe/Moscow")

def msk_day_bounds(day):
    start = datetime.combine(day, time.min, tzinfo=MSK)
    end = start + timedelta(days=1)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

async def main():
    now_msk = datetime.now(MSK)
    today = now_msk.date()
    start, end = msk_day_bounds(today)
    async with async_session() as session:
        eligible = (await session.execute(
            select(func.count(User.id)).where(
                User.is_blocked == False,
                User.daily_card_push == True,
            )
        )).scalar_one()
        sent_today = (await session.execute(
            select(func.count(Notification.id)).where(
                Notification.notification_type == NotificationType.CARD_OF_DAY,
                Notification.is_sent == True,
                Notification.created_at >= start,
                Notification.created_at < end,
            )
        )).scalar_one()
        failed_today = (await session.execute(
            select(func.count(Notification.id)).where(
                Notification.notification_type == NotificationType.CARD_OF_DAY,
                Notification.is_sent == False,
                Notification.created_at >= start,
                Notification.created_at < end,
            )
        )).scalar_one()
        print(f"MSK date={today} eligible_users={eligible} sent_today={sent_today} failed_today={failed_today}")
        rows = (await session.execute(
            select(Notification)
            .where(
                Notification.notification_type == NotificationType.CARD_OF_DAY,
                Notification.created_at >= start,
                Notification.created_at < end,
            )
            .order_by(Notification.created_at.desc())
            .limit(8)
        )).scalars().all()
        for n in rows:
            print(f"  id={n.id} user={n.user_id} sent={n.is_sent} at={n.created_at}")

asyncio.run(main())
PY

echo ""
echo "--- Celery beat schedule ---"
docker compose exec -T celery_beat celery -A app.infrastructure.celery_app inspect scheduled 2>/dev/null | head -20 || true

echo ""
echo "--- Trigger catch-up daily card push now ---"
docker compose exec -T celery_worker celery -A app.infrastructure.celery_app call app.infrastructure.tasks.send_daily_card_push
sleep 5
docker compose logs celery_worker --tail 15 2>&1 | grep -iE 'Daily card|ERROR|Traceback|finished' || true

echo "DONE"
