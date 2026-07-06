#!/bin/bash
set -euo pipefail
cd /opt/taro
SECRET=$(grep '^INTERNAL_API_SECRET=' .env | cut -d= -f2-)

echo "=== pytest payment tests ==="
docker compose exec -T backend python -m pytest tests/test_payment_service.py -v

echo "=== pricing plans ==="
python3 <<'PY'
import json, urllib.request
with urllib.request.urlopen('http://localhost:8000/api/v1/pricing') as resp:
    p = json.load(resp)
plans = p["plans"]
assert len(plans) == 3
assert plans[0]["plan"] == "month_1" and plans[0]["stars"] == 450 and plans[0]["duration_days"] == 30
assert plans[1]["plan"] == "month_3" and plans[1]["stars"] == 1200 and plans[1]["duration_days"] == 90
assert plans[2]["plan"] == "month_6" and plans[2]["stars"] == 2100 and plans[2]["duration_days"] == 180
print("pricing OK:", [(x["plan"], x["stars"], x["duration_days"]) for x in plans])
PY

echo "=== pre-checkout invalid payload ==="
curl -sf -X POST http://localhost:8000/api/v1/payments/telegram/pre-checkout \
  -H 'Content-Type: application/json' \
  -d "{\"secret\":\"${SECRET}\",\"payload\":\"99999999\",\"total_amount\":450,\"currency\":\"XTR\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('ok') is False; print('invalid payment rejected OK')"

echo "=== pre-checkout wrong currency ==="
curl -sf -X POST http://localhost:8000/api/v1/payments/telegram/pre-checkout \
  -H 'Content-Type: application/json' \
  -d "{\"secret\":\"${SECRET}\",\"payload\":\"1\",\"total_amount\":450,\"currency\":\"RUB\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('ok') is False; print('wrong currency rejected OK')"

echo "=== bot->backend connectivity ==="
docker compose exec -T bot python -c "import httpx, os; url=os.getenv('API_URL','http://backend:8000').rstrip('/')+'/health'; r=httpx.get(url,timeout=5); print('bot health', r.status_code, r.text[:80])"

echo "=== ALL PAYMENT CHECKS PASSED ==="
