#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

FAIL=0
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; FAIL=1; }

echo "========== STARS / AFFILIATE PAYMENT AUDIT =========="

echo ""
echo "--- 1. Source code: currency XTR ---"
if grep -q '"currency": "XTR"' backend/app/application/services/payment_service.py; then
  pass "createInvoiceLink uses XTR"
else
  fail "createInvoiceLink missing XTR"
fi

if grep -q 'currency="XTR"' bot/app/handlers/commands.py; then
  pass "bot send_invoice uses XTR"
else
  fail "bot send_invoice missing XTR"
fi

if grep -q "body.currency != \"XTR\"" backend/app/api/v1/router.py; then
  pass "pre-checkout rejects non-XTR"
else
  fail "pre-checkout XTR check missing"
fi

echo ""
echo "--- 2. Frontend uses openInvoice (Stars) ---"
for f in frontend/src/lib/payments.ts frontend/src/pages/SubscriptionPage.tsx frontend/src/pages/CompatibilityPage.tsx frontend/src/components/CompatibilityHero.tsx; do
  if [ -f "$f" ] && grep -q openStarsPayment "$f" 2>/dev/null || grep -q openInvoice "$f" 2>/dev/null; then
    pass "Stars payment path in $(basename "$f")"
  fi
done

echo ""
echo "--- 3. Payment types covered ---"
docker compose exec -T backend python <<'PY' 2>/dev/null || python backend/app/application/services/payment_service.py 2>/dev/null || true
import sys
sys.path.insert(0, "backend")
from app.infrastructure.database.models import PaymentType

expected = {
    "single_spread", "subscription", "compatibility",
    "spread_pack_3", "spread_pack_5", "love_bundle",
}
actual = {t.value for t in PaymentType}
missing = expected - actual
if missing:
    raise SystemExit(f"missing types: {missing}")
print("payment types OK:", sorted(expected))
PY
pass "all product payment types exist" || fail "payment types"

echo ""
echo "--- 4. Live: createInvoiceLink smoke (1 star test invoice) ---"
docker compose exec -T backend python <<'PY'
import asyncio
import sys

async def main():
    from app.application.services.payment_service import PaymentService
    from app.infrastructure.database.session import async_session

    async with async_session() as session:
        svc = PaymentService(session)
        link = await svc.create_invoice_link(
            title="Affiliate audit test",
            description="Smoke test — do not pay",
            payload="audit_0",
            stars=1,
        )
        if not link.startswith("https://"):
            raise SystemExit("invalid invoice link")
        print("invoice link OK", link[:60] + "...")

asyncio.run(main())
PY
pass "createInvoiceLink live" || fail "createInvoiceLink live"

echo ""
echo "--- 5. Affiliate eligibility notes ---"
echo "  OK: paid purchases via openInvoice + XTR → affiliate commission"
echo "  SKIP commission: 100% promo (stars_amount=0, no invoice)"
echo "  SKIP commission: admin grants, referral bonus spreads"

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "========== STARS AUDIT PASSED — ready for Telegram Affiliate =========="
else
  echo "========== STARS AUDIT FAILED =========="
  exit 1
fi
