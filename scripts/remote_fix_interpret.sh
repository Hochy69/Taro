#!/bin/bash
set -euo pipefail
cd /opt/taro
git fetch origin main
git reset --hard origin/main
bash scripts/apply_marketing_enums.sh
docker compose build --no-cache backend frontend celery_worker celery_beat bot
docker compose up -d --build
sleep 40

echo "=== Test interpret spread 13 ==="
docker compose exec -T backend python <<'PY'
import asyncio
from sqlalchemy import select
from app.infrastructure.database.models import Spread, AIResult
from app.infrastructure.database.session import async_session
from app.application.services.spread_service import SpreadService

async def main():
    async with async_session() as session:
        for sid in (13, 15):
            spread = (await session.execute(select(Spread).where(Spread.id == sid))).scalar_one_or_none()
            if not spread:
                print(f"spread {sid}: missing")
                continue
            existing = (await session.execute(select(AIResult).where(AIResult.spread_id == sid))).scalar_one_or_none()
            if existing:
                print(f"spread {sid}: already has ai_result")
                continue
            svc = SpreadService(session)
            ai = await svc.generate_interpretation(sid)
            await session.commit()
            print(f"spread {sid}: interpret OK ai_id={ai.id}")

asyncio.run(main())
PY

curl -sf http://localhost:8000/health && echo " backend ok"
docker compose exec -T backend python -m pytest tests/test_marketing_pushes.py -q
bash scripts/check_marketing_pushes.sh
