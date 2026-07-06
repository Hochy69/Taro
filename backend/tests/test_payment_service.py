"""Payment and subscription period tests."""

from datetime import datetime, timedelta, timezone

import pytest

from app.application.services.payment_service import PLAN_DURATIONS, PLAN_PRICES
from app.core.config import settings
from app.infrastructure.database.models import SubscriptionPlan


def test_subscription_plan_prices_match_settings():
    assert PLAN_PRICES[SubscriptionPlan.MONTH_1] == settings.price_subscription_1m == 450
    assert PLAN_PRICES[SubscriptionPlan.MONTH_3] == settings.price_subscription_3m == 1200
    assert PLAN_PRICES[SubscriptionPlan.MONTH_6] == settings.price_subscription_6m == 2100


def test_subscription_plan_durations():
    assert PLAN_DURATIONS[SubscriptionPlan.MONTH_1] == 30
    assert PLAN_DURATIONS[SubscriptionPlan.MONTH_3] == 90
    assert PLAN_DURATIONS[SubscriptionPlan.MONTH_6] == 180


def test_longer_plans_are_cheaper_per_month():
    per_month_1 = PLAN_PRICES[SubscriptionPlan.MONTH_1] / PLAN_DURATIONS[SubscriptionPlan.MONTH_1]
    per_month_3 = PLAN_PRICES[SubscriptionPlan.MONTH_3] / PLAN_DURATIONS[SubscriptionPlan.MONTH_3]
    per_month_6 = PLAN_PRICES[SubscriptionPlan.MONTH_6] / PLAN_DURATIONS[SubscriptionPlan.MONTH_6]
    assert per_month_3 < per_month_1
    assert per_month_6 < per_month_3


def test_stack_extension_adds_days():
    """Simulate stacking: active 30d sub + 90d purchase => +90 days from current expiry."""
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    current_expires = now + timedelta(days=10)
    purchased_days = PLAN_DURATIONS[SubscriptionPlan.MONTH_3]
    new_expires = current_expires + timedelta(days=purchased_days)
    assert (new_expires - now).days == 100


def test_fresh_subscription_starts_from_now():
    now = datetime(2026, 6, 1, tzinfo=timezone.utc)
    days = PLAN_DURATIONS[SubscriptionPlan.MONTH_6]
    expires = now + timedelta(days=days)
    assert (expires - now).days == 180
