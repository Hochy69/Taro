"""Promo and bundle pricing tests."""

from app.application.services.marketing_service import (
    love_bundle_base_price,
    love_bundle_effective_discount,
    love_bundle_price,
)
from app.application.services.promo_service import discounted_price
from app.core.config import settings


def test_love_bundle_base_is_compat_plus_single():
    assert love_bundle_base_price() == settings.price_compatibility + settings.price_single_spread


def test_love_bundle_default_discount():
    base = love_bundle_base_price()
    assert love_bundle_price() == discounted_price(base, settings.love_bundle_discount_percent)


def test_love_bundle_promo_weaker_than_bundle_uses_bundle():
    assert love_bundle_effective_discount(10) == settings.love_bundle_discount_percent


def test_love_bundle_promo_stronger_than_bundle_uses_promo():
    assert love_bundle_effective_discount(50) == 50


def test_love_bundle_no_promo():
    assert love_bundle_effective_discount(None) == settings.love_bundle_discount_percent


def test_discounted_price_100_percent_free():
    assert discounted_price(99, 100) == 0


def test_discounted_price_never_below_one_unless_free():
    assert discounted_price(2, 50) >= 1


def test_free_spreads_per_period_default():
    assert settings.free_spreads_per_period == 3
