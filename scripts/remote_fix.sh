#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

cp /opt/taro/.env /root/taro.env.bak
rm -rf /opt/taro
git clone https://github.com/Hochy69/Taro.git /opt/taro
cp /root/taro.env.bak /opt/taro/.env

python3 - << 'PY'
from pathlib import Path
p = Path('/opt/taro/frontend/vite.config.ts')
text = p.read_text()
if 'allowedHosts: true' not in text:
    text = text.replace("allowedHosts: ['.tuna.am'],", "allowedHosts: true,")
    p.write_text(text)
print('vite ok')
PY

cat > /etc/caddy/Caddyfile << 'EOF'
s1715822.smartape-vps.com {
    reverse_proxy localhost:5173
}
EOF
systemctl restart caddy

cd /opt/taro
docker compose up -d --build
docker compose ps
curl -sf http://localhost:8000/health && echo " backend ok"
curl -sf -o /dev/null -w "frontend %{http_code}\n" http://localhost:5173/
