#!/bin/bash
set -euo pipefail
cd /opt/taro
git fetch origin main
git reset --hard origin/main
docker compose up -d --build bot
sleep 5
docker compose exec -T bot python -c "from app.handlers.commands import start_keyboard; print(start_keyboard().inline_keyboard[1][0].text)"
