#!/bin/bash
set -euo pipefail
cd /opt/taro
git fetch origin main
git reset --hard origin/main
docker compose build --no-cache frontend bot
docker compose up -d --build
sleep 15
docker compose ps
curl -sf http://localhost:8000/health && echo " backend ok"
curl -sf -o /dev/null -w "https %{http_code}\n" https://91-184-249-229.sslip.io/
