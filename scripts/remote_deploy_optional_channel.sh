#!/bin/bash
set -euo pipefail
cd /opt/taro
git fetch origin main
git reset --hard origin/main

if grep -q '^TELEGRAM_CHANNEL_SUBSCRIBE_REQUIRED=' .env; then
  sed -i 's/^TELEGRAM_CHANNEL_SUBSCRIBE_REQUIRED=.*/TELEGRAM_CHANNEL_SUBSCRIBE_REQUIRED=false/' .env
else
  echo 'TELEGRAM_CHANNEL_SUBSCRIBE_REQUIRED=false' >> .env
fi

docker compose build --no-cache backend bot frontend
docker compose up -d backend bot frontend
sleep 25
docker compose exec -T backend python -m pytest tests/test_channel_subscription.py -q
echo "DEPLOY OK"
