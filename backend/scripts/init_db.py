"""Create all tables for development."""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import text

from app.infrastructure.database.models import Base
from app.infrastructure.database.session import engine

_SCHEMA_PATCHES = [
    "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS birth_lat DOUBLE PRECISION",
    "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS birth_lon DOUBLE PRECISION",
    "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS birth_timezone INTEGER",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_card_push BOOLEAN DEFAULT true",
    "ALTER TABLE limits ADD COLUMN IF NOT EXISTS compatibility_credits INTEGER DEFAULT 0",
    "ALTER TABLE payments ADD COLUMN IF NOT EXISTS original_stars_amount INTEGER",
    "ALTER TABLE payments ADD COLUMN IF NOT EXISTS promo_code_id INTEGER",
    "ALTER TABLE spreads ADD COLUMN IF NOT EXISTS quota_from_bonus BOOLEAN",
]

_ENUM_PATCHES = [
    "ALTER TYPE paymenttype ADD VALUE IF NOT EXISTS 'spread_pack_3'",
    "ALTER TYPE paymenttype ADD VALUE IF NOT EXISTS 'spread_pack_5'",
    "ALTER TYPE paymenttype ADD VALUE IF NOT EXISTS 'love_bundle'",
]


async def ensure_schema():
    async with engine.begin() as conn:
        for stmt in _SCHEMA_PATCHES:
            await conn.execute(text(stmt))
        for stmt in _ENUM_PATCHES:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_schema()
    print("Tables created")


if __name__ == "__main__":
    asyncio.run(create_tables())
