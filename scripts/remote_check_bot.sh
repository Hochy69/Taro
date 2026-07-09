#!/bin/bash
set -euo pipefail
cd /opt/taro
TOKEN=$(grep '^TELEGRAM_BOT_TOKEN=' .env | cut -d= -f2-)
USER=$(grep '^TELEGRAM_BOT_USERNAME=' .env | cut -d= -f2-)

echo "=== .env bot username: $USER ==="
echo "=== getMe ==="
curl -s "https://api.telegram.org/bot${TOKEN}/getMe" | python3 -m json.tool

echo ""
echo "=== docker bot status ==="
docker compose ps bot --format 'table {{.Name}}\t{{.Status}}'

echo ""
echo "=== bot logs (last 30) ==="
docker compose logs bot --tail 30 2>&1

echo ""
echo "=== webhook info (should be empty for polling) ==="
curl -s "https://api.telegram.org/bot${TOKEN}/getWebhookInfo" | python3 -m json.tool
