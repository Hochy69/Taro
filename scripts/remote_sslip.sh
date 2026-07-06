#!/bin/bash
set -euo pipefail

DOMAIN="91-184-249-229.sslip.io"
URL="https://${DOMAIN}"

sed -i "s|^FRONTEND_URL=.*|FRONTEND_URL=${URL}|" /opt/taro/.env
sed -i "s|^TELEGRAM_WEBAPP_URL=.*|TELEGRAM_WEBAPP_URL=${URL}|" /opt/taro/.env

cat > /etc/caddy/Caddyfile << EOF
${DOMAIN} {
    reverse_proxy localhost:5173
}
EOF

systemctl restart caddy
cd /opt/taro
docker compose restart bot backend

sleep 8
curl -sf http://localhost:8000/health && echo " backend ok"
curl -sf -o /dev/null -w "https %{http_code}\n" "https://${DOMAIN}/"
