#!/bin/bash
set -euo pipefail
cd /opt/taro
git fetch origin main
git reset --hard origin/main

docker compose restart backend bot frontend
sleep 25

echo "=== migrate ==="
docker compose exec -T backend alembic upgrade head

echo "=== tests ==="
docker compose exec -T backend python -m pytest tests/test_attribution.py -q

echo "=== attribution flow ==="
docker compose exec -T backend python - <<'PY'
import asyncio
import httpx
from sqlalchemy import select
from app.core.config import settings
from app.core.security import create_admin_token
from app.infrastructure.database.models import User
from app.infrastructure.database.session import async_session

async def main():
    secret = settings.internal_api_secret
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30) as client:
        r = await client.post(
            "/api/v1/attribution/pending",
            json={"telegram_id": 900000777, "source": "p_testchannel", "secret": secret},
        )
        print("pending", r.status_code, r.json())
        assert r.status_code == 200 and r.json().get("source") == "p_testchannel"

        # Create or update user with source via pending apply path
        async with async_session() as db:
            from app.application.services.attribution_service import AttributionService
            from app.infrastructure.database.models import Profile, UserLimit
            result = await db.execute(select(User).where(User.telegram_id == 900000777))
            user = result.scalar_one_or_none()
            if not user:
                user = User(telegram_id=900000777, username="partner_test", first_name="Partner")
                db.add(user)
                await db.flush()
                db.add(Profile(user_id=user.id, name="Partner"))
                db.add(UserLimit(user_id=user.id))
                await db.flush()
            await AttributionService(db).apply_to_user(user, None)
            await db.commit()
            print("user source", user.acquisition_source)
            assert user.acquisition_source == "p_testchannel"
            admin = (await db.execute(select(User).where(User.is_admin.is_(True)).limit(1))).scalar_one()
            token = create_admin_token(admin.id)

        pr = await client.get("/api/v1/admin/partners", headers={"Authorization": f"Bearer {token}"})
        print("partners HTTP", pr.status_code)
        assert pr.status_code == 200
        rows = pr.json()
        assert any(x["source"] == "p_testchannel" for x in rows), rows
        print("partners ok", [x["source"] for x in rows])

asyncio.run(main())
PY

curl -sf http://localhost:8000/health
echo
echo "ATTRIBUTION DEPLOY OK"
