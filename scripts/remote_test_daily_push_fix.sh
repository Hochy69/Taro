#!/bin/bash
set -euo pipefail
cd /opt/taro
git fetch origin main
git reset --hard origin/main
docker compose build --no-cache backend celery_worker celery_beat
docker compose up -d backend celery_worker celery_beat
sleep 25

echo "========== PYTEST =========="
docker compose exec -T backend python -m pytest tests/ -q

echo ""
echo "========== NOTIFICATION AUDIT =========="
bash scripts/audit_notifications.sh

echo ""
echo "========== DAILY PUSH SMOKE =========="
docker compose exec -T celery_worker celery -A app.infrastructure.celery_app call app.infrastructure.tasks.send_daily_card_push
sleep 5
docker compose logs celery_worker --tail 12 2>&1 | grep -iE 'Daily card push|RuntimeError|different loop|finished' || true

echo "ALL DONE"
