#!/bin/bash
set -euo pipefail
cd /opt/taro

docker compose exec -T backend python <<'PY'
import asyncio
import traceback
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.infrastructure.database.models import Spread, User
from app.infrastructure.database.session import async_session
from app.application.services.spread_service import SpreadService
from app.application.services.marketing_push_service import on_spread_interpreted

async def test(spread_id: int):
    async with async_session() as session:
        spread = (await session.execute(
            select(Spread).options(selectinload(Spread.ai_result)).where(Spread.id == spread_id)
        )).scalar_one_or_none()
        if not spread:
            print(f"spread {spread_id} not found")
            return
        print(f"spread {spread_id} status={spread.status.value} ai_result={spread.ai_result is not None}")
        svc = SpreadService(session)
        try:
            ai = await svc.generate_interpretation(spread_id)
            print("generate OK", ai.id if ai else None)
            await on_spread_interpreted(session, spread_id)
            print("marketing OK")
            await session.commit()
            print("commit OK")
        except Exception as e:
            print("ERROR:", type(e).__name__, e)
            traceback.print_exc()
            await session.rollback()

async def main():
    for sid in (13, 15):
        print("=" * 40, sid)
        await test(sid)

asyncio.run(main())
PY
