#!/bin/bash
set -euo pipefail
cd /opt/taro
git fetch origin main
git reset --hard origin/main
docker compose up -d --build backend bot frontend
sleep 50
echo "=== pytest ==="
docker compose exec -T backend python -m pytest tests/test_payment_service.py tests/test_promo_marketing.py -v
echo "=== payment smoke ==="
bash scripts/test_payments_vps.sh
echo "=== health ==="
curl -sf http://localhost:8000/health && echo " backend ok"
curl -sf -o /dev/null -w "frontend:%{http_code}\n" http://localhost:5173/
