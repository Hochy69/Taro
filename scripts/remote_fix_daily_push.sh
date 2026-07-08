#!/bin/bash
set -euo pipefail
cd /opt/taro
docker compose build --no-cache celery_worker celery_beat
docker compose up -d celery_worker celery_beat
sleep 20
echo "--- Trigger daily card push (catch-up) ---"
docker compose exec -T celery_worker celery -A app.infrastructure.celery_app call app.infrastructure.tasks.send_daily_card_push
sleep 8
docker compose logs celery_worker --tail 20 2>&1 | grep -iE 'Daily card push|ERROR|Traceback|finished' || true
docker compose exec -T backend python <<'PY'
import asyncio
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select, func

from app.infrastructure.database.models import Notification, NotificationType
from app.infrastructure.database.session import async_session

MSK = ZoneInfo("Europe/Moscow")

async def main():
    today = datetime.now(MSK).date()
    start = datetime.combine(today, time.min, tzinfo=MSK).astimezone(timezone.utc)
    end = start + timedelta(days=1)
    async with async_session() as session:
        sent = (await session.execute(
            select(func.count(Notification.id)).where(
                Notification.notification_type == NotificationType.CARD_OF_DAY,
                Notification.is_sent == True,
                Notification.created_at >= start,
                Notification.created_at < end,
            )
        )).scalar_one()
        print(f"CARD_OF_DAY sent today (MSK): {sent}")

asyncio.run(main())
PY
