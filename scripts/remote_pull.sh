#!/bin/bash
set -euo pipefail
cd /opt/taro
git fetch origin main
git reset --hard origin/main
docker compose build --no-cache backend bot frontend celery_worker celery_beat
docker compose up -d --build
echo "=== DB enum patches ==="
bash scripts/apply_marketing_enums.sh
sleep 35
docker compose ps
curl -sf http://localhost:8000/health && echo " backend ok"
curl -sf -o /dev/null -w "https %{http_code}\n" https://91-184-249-229.sslip.io/
