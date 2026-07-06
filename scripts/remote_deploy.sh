#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
LOG=/root/taro-deploy.log
exec > >(tee -a "$LOG") 2>&1

echo "=== $(date) deploy start ==="

if ! command -v docker >/dev/null 2>&1; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
fi

apt-get update -y
apt-get install -y git curl ufw ca-certificates python3 gnupg debian-keyring debian-archive-keyring apt-transport-https

ufw allow OpenSSH || true
ufw allow 80/tcp || true
ufw allow 443/tcp || true
ufw --force enable || true

if ! command -v caddy >/dev/null 2>&1; then
  echo "Installing Caddy..."
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -y
  apt-get install -y caddy
fi

mkdir -p /opt/taro
if [ -d /opt/taro/.git ]; then
  cd /opt/taro && git pull
else
  git clone https://github.com/Hochy69/Taro.git /opt/taro
fi
cd /opt/taro

python3 - << 'PY'
from pathlib import Path
p = Path('/opt/taro/frontend/vite.config.ts')
text = p.read_text()
if 'allowedHosts: true' not in text:
    text = text.replace("allowedHosts: ['.tuna.am'],", "allowedHosts: true,")
    p.write_text(text)
print('vite patched')
PY

cat > /etc/caddy/Caddyfile << 'CADDYEOF'
s1715822.smartape-vps.com {
    reverse_proxy localhost:5173
}
CADDYEOF
systemctl enable caddy
systemctl restart caddy

docker compose up -d --build

docker compose ps
curl -sf http://localhost:8000/health && echo " backend ok"
curl -sf -o /dev/null -w "frontend %{http_code}\n" http://localhost:5173/

echo "=== $(date) deploy done ==="
