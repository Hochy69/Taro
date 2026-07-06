#!/bin/bash
set -euo pipefail
cd /opt/taro
SECRET=$(grep '^INTERNAL_API_SECRET=' .env | cut -d= -f2-)
FAIL=0

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; FAIL=1; }

echo "========== MARKETING PUSH CHECK =========="

docker compose exec -T backend python -m pytest tests/test_marketing_pushes.py -q && pass "marketing push unit tests" || fail "marketing push unit tests"

echo ""
echo "--- Notification enum values ---"
docker compose exec -T backend python <<'PY'
from app.infrastructure.database.models import NotificationType
required = {
    "start_no_webapp", "spread_first", "spread_second", "spread_third",
    "free_limit_hit", "free_limit_followup", "compat_view_abandoned",
    "compat_paid_upsell", "weekly_referral",
}
values = {t.value for t in NotificationType}
missing = required - values
assert not missing, f"missing enum values: {missing}"
print("enum OK", len(required), "marketing types")
PY
pass "notification enum" || fail "notification enum"

echo ""
echo "--- Internal API: bot-start ---"
CODE=$(curl -s -o /tmp/bot_start_bad.json -w "%{http_code}" -X POST http://localhost:8000/api/v1/notifications/bot-start \
  -H 'Content-Type: application/json' \
  -d '{"telegram_id":1,"secret":"wrong"}')
[ "$CODE" = "403" ] && pass "bot-start bad secret -> 403" || fail "bot-start bad secret -> $CODE"

curl -sf -X POST http://localhost:8000/api/v1/notifications/bot-start \
  -H 'Content-Type: application/json' \
  -d "{\"telegram_id\":999888777,\"secret\":\"${SECRET}\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('ok') is True" && pass "bot-start schedules reminder" || fail "bot-start"

echo ""
echo "--- Celery beat schedule ---"
docker compose exec -T celery_beat celery -A app.infrastructure.celery_app inspect scheduled 2>/dev/null | head -5 || true
docker compose exec -T backend python <<'PY'
from app.infrastructure.celery_app import celery_app
tasks = celery_app.conf.beat_schedule
assert "send-weekly-referral-push" in tasks
assert "send-daily-card-push" in tasks
print("beat schedule OK", list(tasks.keys()))
PY
pass "celery beat marketing tasks" || fail "celery beat"

echo ""
bash scripts/check_notifications.sh

if [ "$FAIL" -eq 0 ]; then
  echo "========== MARKETING PUSH CHECKS PASSED =========="
else
  echo "========== MARKETING PUSH CHECKS FAILED =========="
  exit 1
fi
