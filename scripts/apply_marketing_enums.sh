#!/bin/bash
set -euo pipefail
cd /opt/taro

echo "=== Apply marketing notification enum patches ==="
docker compose exec -T backend python <<'PY'
import asyncio
from sqlalchemy import text
from app.infrastructure.database.session import engine

_PATCHES = [
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'START_NO_WEBAPP'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'SPREAD_FIRST'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'SPREAD_SECOND'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'SPREAD_THIRD'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'FREE_LIMIT_HIT'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'FREE_LIMIT_FOLLOWUP'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'COMPAT_VIEW_ABANDONED'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'COMPAT_PAID_UPSELL'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'WEEKLY_REFERRAL'",
]


async def main() -> None:
    async with engine.begin() as conn:
        for stmt in _PATCHES:
            try:
                await conn.execute(text(stmt))
            except Exception as exc:
                print("skip/fail:", stmt[:60], exc)

asyncio.run(main())
print("enum patches OK")
PY

echo "=== Restart celery ==="
docker compose restart celery_worker celery_beat bot
sleep 10
docker compose ps
