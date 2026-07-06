#!/bin/bash
set -euo pipefail
cd /opt/taro

docker compose exec -T backend python <<'PY'
import asyncio
import httpx
from app.core.config import settings

async def main():
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "http://localhost:8000/api/v1/admin/grant",
            json={
                "internal_secret": settings.internal_api_secret,
                "word": settings.admin_secret_word,
                "telegram_id": 555000111,
                "username": "admintest",
                "first_name": "AdminTest",
            },
        )
        print("grant", r.status_code, r.text[:400])
        if r.status_code != 200:
            return
        token = r.json()["admin_token"]
        for path in ("/dashboard", "/users", "/finance"):
            r2 = await client.get(
                f"http://localhost:8000/api/v1/admin{path}",
                headers={"Authorization": f"Bearer {token}"},
            )
            print(path, r2.status_code, r2.text[:150])
        r3 = await client.get(
            "http://frontend:5173/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        print("frontend_proxy", r3.status_code, r3.text[:150])
        print("TOKEN_FOR_BROWSER", token)

asyncio.run(main())
PY
