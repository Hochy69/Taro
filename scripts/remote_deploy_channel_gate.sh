#!/bin/bash
set -euo pipefail
cd /opt/taro
git fetch origin main
git reset --hard origin/main

if grep -q '^TELEGRAM_REQUIRED_CHANNEL=' .env; then
  sed -i 's/^TELEGRAM_REQUIRED_CHANNEL=.*/TELEGRAM_REQUIRED_CHANNEL=best1taro/' .env
else
  echo 'TELEGRAM_REQUIRED_CHANNEL=best1taro' >> .env
fi

docker compose build --no-cache backend bot frontend
docker compose up -d backend bot frontend
sleep 30
curl -sf http://localhost:8000/health && echo " backend ok"
docker compose exec -T backend python -m pytest tests/test_channel_subscription.py tests/test_marketing_pushes.py -q
echo "DEPLOY OK"
