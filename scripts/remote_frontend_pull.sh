#!/bin/bash
set -euo pipefail
cd /opt/taro
git fetch origin main
git reset --hard origin/main
docker compose build --no-cache frontend
docker compose up -d frontend
sleep 25
curl -sf -o /dev/null -w "frontend %{http_code}\n" http://localhost:5173/
