#!/bin/bash
set -euo pipefail
cd /opt/taro
git fetch origin main
git reset --hard origin/main
docker compose restart backend
sleep 20

echo "=== import check ==="
docker compose exec -T backend python - <<'PY'
from app.api.v1.router import card_of_day
from app.application.services.card_of_day_service import get_card_of_day
print("imports ok", get_card_of_day.__name__)
PY

echo "=== live card-of-day with auth ==="
docker compose exec -T backend python - <<'PY'
import asyncio
from datetime import datetime, timezone

from jose import jwt
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.infrastructure.database.models import User
from app.infrastructure.database.session import AsyncSessionLocal
from app.application.services.card_of_day_service import get_card_of_day
import httpx


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).options(selectinload(User.profile)).order_by(User.id).limit(1)
        )
        user = result.scalar_one()
        name = user.profile.name if user.profile and user.profile.name else (user.first_name or "друг")
        zodiac = user.profile.zodiac_sign if user.profile else None
        data = await get_card_of_day(db, user.id, name, zodiac)
        print("service ok:", data["card"]["name"], data["date"])

        token = jwt.encode(
            {
                "sub": str(user.id),
                "telegram_id": user.telegram_id,
                "exp": datetime.now(timezone.utc).timestamp() + 3600,
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        r = await client.get(
            "/api/v1/card-of-day",
            headers={"Authorization": f"Bearer {token}"},
        )
        print("HTTP", r.status_code)
        body = r.json()
        if r.status_code != 200:
            print(body)
            raise SystemExit(1)
        print("api ok:", body["card"]["name"], body["date"])
        assert body["meaning"]
        assert body["advice"]
        assert body["text"]

asyncio.run(main())
PY

curl -sf http://localhost:8000/health
echo
echo "FIX OK"
