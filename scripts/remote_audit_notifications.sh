#!/bin/bash
set -euo pipefail
cd /opt/taro
git fetch origin main
git reset --hard origin/main
bash scripts/apply_marketing_enums.sh
docker compose build --no-cache backend celery_worker celery_beat bot
docker compose up -d --build
sleep 35
bash scripts/audit_notifications.sh
