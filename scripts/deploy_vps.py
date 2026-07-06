#!/usr/bin/env python3
"""One-shot VPS deployment helper. Run locally; do not commit credentials."""
import secrets
import sys
import time

import paramiko

HOST = "91.184.249.229"
USER = "root"
PASSWORD = sys.argv[1] if len(sys.argv) > 1 else ""
DOMAIN = "s1715822.smartape-vps.com"
URL = f"https://{DOMAIN}"
BOT_TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""
BOT_USER = "best1tarolog_bot"

if not PASSWORD or not BOT_TOKEN:
    print("Usage: python deploy_vps.py <root_password> <telegram_bot_token>", file=sys.stderr)
    sys.exit(1)


def gen() -> str:
    return secrets.token_hex(32)


ENV_CONTENT = f"""# Production .env
APP_NAME=Tarot Mini App
APP_ENV=production
DEBUG=false
SECRET_KEY={gen()}
API_URL=http://backend:8000
FRONTEND_URL={URL}

DATABASE_URL=postgresql+asyncpg://tarot:tarot_secret@postgres:5432/tarot_db
REDIS_URL=redis://redis:6379/0

JWT_SECRET_KEY={gen()}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

TELEGRAM_BOT_TOKEN={BOT_TOKEN}
TELEGRAM_BOT_USERNAME={BOT_USER}
TELEGRAM_WEBAPP_URL={URL}
TELEGRAM_PAYMENT_PROVIDER_TOKEN=

AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini
TEMPLATE_ONLY=true
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

ADMIN_JWT_SECRET={gen()}
ADMIN_SECRET_WORD=TaroVlad
FIRST_ADMIN_TELEGRAM_ID=

CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

FREE_DAILY_SPREADS=1
PREMIUM_DAILY_SPREADS=15
FREE_HISTORY_LIMIT=5

PRICE_SINGLE_SPREAD=69
PRICE_SUBSCRIPTION_1M=450
PRICE_SUBSCRIPTION_3M=1200
PRICE_SUBSCRIPTION_6M=2100
PRICE_COMPATIBILITY=99
PRICE_SPREAD_PACK_3=249
PRICE_SPREAD_PACK_5=399
FIRST_PAID_DISCOUNT_PERCENT=30
LOVE_BUNDLE_DISCOUNT_PERCENT=20
REFERRAL_PREMIUM_TRIAL_DAYS=3

INTERNAL_API_SECRET={gen()}
"""

REMOTE_SCRIPT = f"""set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo '=== System update ==='
apt-get update -y
apt-get upgrade -y

echo '=== Install packages ==='
apt-get install -y git curl ufw ca-certificates python3

echo '=== Install Docker ==='
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
fi

echo '=== Firewall ==='
ufw allow OpenSSH || true
ufw allow 80/tcp || true
ufw allow 443/tcp || true
ufw --force enable || true

echo '=== Install Caddy ==='
if ! command -v caddy >/dev/null 2>&1; then
  apt-get install -y debian-keyring debian-archive-keyring apt-transport-https gnupg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -y
  apt-get install -y caddy
fi

echo '=== Clone project ==='
mkdir -p /opt/taro
if [ -d /opt/taro/.git ]; then
  cd /opt/taro && git pull
else
  git clone https://github.com/Hochy69/Taro.git /opt/taro
fi
cd /opt/taro

echo '=== Write .env ==='
cat > /opt/taro/.env << 'ENVEOF'
{ENV_CONTENT}ENVEOF

echo '=== Patch vite allowedHosts ==='
python3 - << 'PY'
from pathlib import Path
p = Path('/opt/taro/frontend/vite.config.ts')
text = p.read_text()
if 'allowedHosts: true' not in text:
    text = text.replace("allowedHosts: ['.tuna.am'],", "allowedHosts: true,")
    p.write_text(text)
print('vite patched')
PY

echo '=== Caddy config ==='
cat > /etc/caddy/Caddyfile << 'CADDYEOF'
{DOMAIN} {{
    reverse_proxy localhost:5173
}}
CADDYEOF
systemctl enable caddy
systemctl reload caddy || systemctl restart caddy

echo '=== Docker compose up ==='
docker compose up -d --build

echo '=== Status ==='
docker compose ps
curl -sf http://localhost:8000/health && echo ' backend ok'
curl -sf -o /dev/null -w '%{{http_code}}\\n' http://localhost:5173/
"""


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    transport = client.get_transport()
    channel = transport.open_session()
    channel.get_pty()
    channel.exec_command("bash -s")
    channel.send(REMOTE_SCRIPT.encode())
    channel.shutdown_write()

    start = time.time()
    while True:
        if channel.recv_ready():
            sys.stdout.buffer.write(channel.recv(8192))
            sys.stdout.buffer.flush()
        if channel.recv_stderr_ready():
            sys.stderr.buffer.write(channel.recv_stderr(8192))
            sys.stderr.buffer.flush()
        if channel.exit_status_ready():
            while channel.recv_ready():
                sys.stdout.buffer.write(channel.recv(8192))
            while channel.recv_stderr_ready():
                sys.stderr.buffer.write(channel.recv_stderr(8192))
            break
        if time.time() - start > 1800:
            print("TIMEOUT", file=sys.stderr)
            return 1
        time.sleep(0.3)

    code = channel.recv_exit_status()
    client.close()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
