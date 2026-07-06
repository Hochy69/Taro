#!/bin/bash
set -euo pipefail
cd /opt/taro
docker compose exec -T backend python <<'PY'
import asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings
from app.infrastructure.database.models import Payment, Subscription, User, UserLimit, Profile

TEST_TG = 999999001

async def main():
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        user = (await db.execute(select(User).where(User.telegram_id == TEST_TG))).scalar_one_or_none()
        if not user:
            print("no test user to clean")
            return
        uid = user.id
        await db.execute(delete(Payment).where(Payment.user_id == uid))
        await db.execute(delete(Subscription).where(Subscription.user_id == uid))
        await db.execute(delete(UserLimit).where(UserLimit.user_id == uid))
        prof = (await db.execute(select(Profile).where(Profile.user_id == uid))).scalar_one_or_none()
        if prof:
            await db.delete(prof)
        await db.delete(user)
        await db.commit()
        print("removed QA user", TEST_TG)
    await engine.dispose()

asyncio.run(main())
PY
