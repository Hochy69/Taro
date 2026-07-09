#!/bin/bash
set -euo pipefail
cd /opt/taro

echo "========== RECENT INTERPRET ERRORS =========="
docker compose logs backend --tail 200 2>&1 | grep -iE 'interpret|generation failed|500|error|traceback' | tail -40 || echo "(no matches)"

echo ""
echo "========== FAILED / GENERATING SPREADS =========="
docker compose exec -T backend python <<'PY'
import asyncio
from sqlalchemy import select
from app.infrastructure.database.models import Spread, SpreadStatus, User
from app.infrastructure.database.session import async_session

async def main():
    async with async_session() as session:
        for status in (SpreadStatus.FAILED, SpreadStatus.GENERATING):
            rows = (await session.execute(
                select(Spread, User.telegram_id, User.first_name)
                .join(User, User.id == Spread.user_id)
                .where(Spread.status == status)
                .order_by(Spread.id.desc())
                .limit(10)
            )).all()
            print(f"\n{status.value}: {len(rows)} recent")
            for spread, tg_id, name in rows:
                print(f"  spread_id={spread.id} user={name} tg={tg_id} created={spread.created_at}")

asyncio.run(main())
PY

echo ""
echo "========== SPREADS WITHOUT AI RESULT (completed/pending) =========="
docker compose exec -T backend python <<'PY'
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.infrastructure.database.models import Spread, SpreadStatus, AIResult, User
from app.infrastructure.database.session import async_session

async def main():
    async with async_session() as session:
        rows = (await session.execute(
            select(Spread, User.telegram_id, User.first_name)
            .join(User, User.id == Spread.user_id)
            .outerjoin(AIResult, AIResult.spread_id == Spread.id)
            .where(AIResult.id.is_(None), Spread.status.in_([SpreadStatus.PENDING, SpreadStatus.GENERATING, SpreadStatus.FAILED]))
            .order_by(Spread.id.desc())
            .limit(15)
        )).all()
        for spread, tg_id, name in rows:
            print(f"  spread_id={spread.id} status={spread.status.value} user={name} tg={tg_id}")

asyncio.run(main())
PY
