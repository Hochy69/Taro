"""Ensure paid flows use Telegram Stars (required for Telegram Affiliate Program)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_payment_service_uses_xtr():
    text = (ROOT / "backend/app/application/services/payment_service.py").read_text(encoding="utf-8")
    assert '"currency": "XTR"' in text
    assert "createInvoiceLink" in text


def test_bot_pre_checkout_enforces_xtr():
    router = (ROOT / "backend/app/api/v1/router.py").read_text(encoding="utf-8")
    assert 'body.currency != "XTR"' in router


def test_frontend_uses_open_invoice():
    payments = (ROOT / "frontend/src/lib/payments.ts").read_text(encoding="utf-8")
    assert "openInvoice" in payments
    assert "createPayment" in payments


def test_free_promo_skips_invoice():
    """100% promo completes without invoice — documented affiliate exclusion."""
    router = (ROOT / "backend/app/api/v1/router.py").read_text(encoding="utf-8")
    assert "complete_free_payment" in router
    assert "invoice_link=None" in router
