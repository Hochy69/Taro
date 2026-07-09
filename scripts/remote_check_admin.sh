#!/bin/bash
set -euo pipefail
cd /opt/taro
FAIL=0
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; FAIL=1; }

SECRET=$(grep '^INTERNAL_API_SECRET=' .env | cut -d= -f2-)
WORD=$(grep '^ADMIN_SECRET_WORD=' .env | cut -d= -f2-)
WORD=${WORD:-TaroVlad}
FRONT=$(grep '^FRONTEND_URL=' .env | cut -d= -f2- | tr -d '\r')
FRONT=${FRONT:-https://91-184-249-229.sslip.io}

echo "========== ADMIN PANEL CHECK =========="
echo "frontend=$FRONT word_set=$([ -n "$WORD" ] && echo yes || echo no)"

echo ""
echo "--- 1. Services ---"
for svc in taro-backend-1 taro-frontend-1 taro-bot-1; do
  if docker compose ps --status running --format '{{.Name}}' | grep -qx "$svc"; then
    pass "running $svc"
  else
    fail "not running $svc"
  fi
done

echo ""
echo "--- 2. Grant rejects bad secret ---"
CODE=$(curl -s -o /tmp/admin_bad.json -w "%{http_code}" -X POST http://localhost:8000/api/v1/admin/grant \
  -H 'Content-Type: application/json' \
  -d '{"internal_secret":"wrong","telegram_id":1,"word":"x"}')
[ "$CODE" = "403" ] && pass "grant bad secret -> 403" || fail "grant bad secret -> $CODE"

echo ""
echo "--- 3. Grant rejects wrong word ---"
CODE=$(curl -s -o /tmp/admin_badword.json -w "%{http_code}" -X POST http://localhost:8000/api/v1/admin/grant \
  -H 'Content-Type: application/json' \
  -d "{\"internal_secret\":\"${SECRET}\",\"telegram_id\":1,\"word\":\"WrongWord\"}")
[ "$CODE" = "403" ] && pass "grant bad word -> 403" || fail "grant bad word -> $CODE"

echo ""
echo "--- 4. Grant with correct secret+word ---"
# Use a dedicated test telegram id that won't collide with real users badly
RESP=$(curl -s -X POST http://localhost:8000/api/v1/admin/grant \
  -H 'Content-Type: application/json' \
  -d "{\"internal_secret\":\"${SECRET}\",\"telegram_id\":900000001,\"word\":\"${WORD}\",\"username\":\"admin_check\",\"first_name\":\"AdminCheck\"}")
echo "$RESP" | python3 -c "
import sys, json
d=json.load(sys.stdin)
assert d.get('granted') is True, d
assert d.get('admin_token'), d
assert '/admin' in (d.get('admin_url') or ''), d
print('token_len', len(d['admin_token']))
print('admin_url', d['admin_url'][:80]+'...')
open('/tmp/admin_token.txt','w').write(d['admin_token'])
"
pass "grant OK"

TOKEN=$(cat /tmp/admin_token.txt)

echo ""
echo "--- 5. Admin ping ---"
PING=$(curl -s -o /tmp/admin_ping.json -w "%{http_code}" http://localhost:8000/api/v1/admin/ping \
  -H "Authorization: Bearer ${TOKEN}")
[ "$PING" = "200" ] && pass "ping 200" || fail "ping -> $PING $(cat /tmp/admin_ping.json)"
python3 -c "import json; d=json.load(open('/tmp/admin_ping.json')); assert d.get('ok') is True; print(d)"

echo ""
echo "--- 6. Dashboard ---"
DASH=$(curl -s -o /tmp/admin_dash.json -w "%{http_code}" http://localhost:8000/api/v1/admin/dashboard \
  -H "Authorization: Bearer ${TOKEN}")
[ "$DASH" = "200" ] && pass "dashboard 200" || fail "dashboard -> $DASH"
python3 - <<'PY'
import json
d=json.load(open('/tmp/admin_dash.json'))
required=['total_users','dau','mau','premium_users','total_revenue_stars','total_spreads']
missing=[k for k in required if k not in d]
if missing:
    raise SystemExit(f'missing keys: {missing}')
print({k:d[k] for k in required})
PY
pass "dashboard payload"

echo ""
echo "--- 7. Users list ---"
USERS=$(curl -s -o /tmp/admin_users.json -w "%{http_code}" "http://localhost:8000/api/v1/admin/users?limit=5" \
  -H "Authorization: Bearer ${TOKEN}")
[ "$USERS" = "200" ] && pass "users 200" || fail "users -> $USERS"
python3 -c "import json; u=json.load(open('/tmp/admin_users.json')); assert isinstance(u,list); print('users', len(u)); print(u[0] if u else 'empty')"

echo ""
echo "--- 8. Finance ---"
FIN=$(curl -s -o /tmp/admin_fin.json -w "%{http_code}" http://localhost:8000/api/v1/admin/finance \
  -H "Authorization: Bearer ${TOKEN}")
[ "$FIN" = "200" ] && pass "finance 200" || fail "finance -> $FIN"
python3 -c "import json; d=json.load(open('/tmp/admin_fin.json')); assert 'revenue_day' in d and 'currency' in d; print(d)"

echo ""
echo "--- 9. Unauthorized without token ---"
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/admin/dashboard)
[ "$CODE" = "401" ] && pass "dashboard no token -> 401" || fail "dashboard no token -> $CODE"

echo ""
echo "--- 10. Frontend /admin page ---"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "${FRONT}/admin")
[ "$CODE" = "200" ] && pass "frontend /admin -> 200" || fail "frontend /admin -> $CODE"

# Check that admin JS bundle is referenced / page loads HTML
curl -s "${FRONT}/admin" | grep -qi 'root\|html' && pass "frontend /admin HTML" || fail "frontend /admin HTML"

echo ""
echo "--- 11. Unit tests admin_stats ---"
docker compose exec -T backend python -m pytest tests/test_admin_stats.py -q && pass "pytest admin_stats" || fail "pytest admin_stats"

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "========== ADMIN PANEL CHECK PASSED =========="
else
  echo "========== ADMIN PANEL CHECK FAILED =========="
  exit 1
fi
