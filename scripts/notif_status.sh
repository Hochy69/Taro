#!/bin/bash
set -euo pipefail
cd /opt/taro
docker compose exec -T backend python <<'PY'
import asyncio
from sqlalchemy import select, func
from app.infrastructure.database.models import Notification, User
from app.infrastructure.database.session import async_session

async def main():
    async with async_session() as session:
        total = (await session.execute(select(func.count(Notification.id)))).scalar_one()
        sent = (await session.execute(select(func.count(Notification.id)).where(Notification.is_sent == True))).scalar_one()
        failed = (await session.execute(select(func.count(Notification.id)).where(Notification.is_sent == False))).scalar_one()
        print(f"notifications total={total} sent={sent} failed={failed}")
        rows = (await session.execute(
            select(Notification).order_by(Notification.created_at.desc()).limit(10)
        )).scalars().all()
        for n in rows:
            print(f"  user={n.user_id} type={n.notification_type.value} sent={n.is_sent}")

asyncio.run(main())
PY
docker compose logs celery_worker --tail 15
