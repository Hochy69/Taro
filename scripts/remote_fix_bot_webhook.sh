#!/bin/bash
set -euo pipefail
cd /opt/taro
TOKEN=$(grep '^TELEGRAM_BOT_TOKEN=' .env | cut -d= -f2-)

echo "=== Current webhook ==="
curl -s "https://api.telegram.org/bot${TOKEN}/getWebhookInfo" | python3 -m json.tool

echo ""
echo "=== Delete webhook (ControllerBot hijack) ==="
curl -s "https://api.telegram.org/bot${TOKEN}/deleteWebhook?drop_pending_updates=true" | python3 -m json.tool

echo ""
echo "=== Restart bot ==="
docker compose restart bot
sleep 8

echo ""
echo "=== Verify webhook cleared ==="
curl -s "https://api.telegram.org/bot${TOKEN}/getWebhookInfo" | python3 -m json.tool

echo ""
echo "=== Bot logs after restart ==="
docker compose logs bot --tail 8 2>&1
