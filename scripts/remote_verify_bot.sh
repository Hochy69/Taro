#!/bin/bash
sleep 5
cd /opt/taro
docker compose logs bot --tail 10 2>&1
TOKEN=$(grep '^TELEGRAM_BOT_TOKEN=' .env | cut -d= -f2-)
curl -s "https://api.telegram.org/bot${TOKEN}/getWebhookInfo" | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print('webhook_url=', repr(r.get('url','')))"
