#!/bin/bash
set -euo pipefail
cd /opt/taro

echo "=== Apply marketing notification enum patches ==="
docker compose exec -T backend python <<'PY'
import asyncio
from sqlalchemy import text
from app.infrastructure.database.session import engine

_PATCHES = [
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'start_no_webapp'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'spread_first'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'spread_second'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'spread_third'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'free_limit_hit'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'free_limit_followup'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'compat_view_abandoned'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'compat_paid_upsell'",
    "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'weekly_referral'",
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
