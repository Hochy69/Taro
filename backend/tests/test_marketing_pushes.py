"""Tests for marketing push copy."""

from app.application.services import push_messages as copy
from app.core.config import settings


def test_start_no_webapp_message():
    assert "первого расклада" in copy.start_no_webapp_message()
    assert "3 бесплатные" in copy.start_no_webapp_message()


def test_free_limit_exhausted_includes_prices():
    msg = copy.free_limit_exhausted_message()
    assert str(settings.price_single_spread) in msg
    assert str(settings.free_spread_period_days) in msg


def test_after_first_spread_mentions_compat():
    assert "Что между вами" in copy.after_first_spread_message()
    assert "2 из 3" in copy.after_first_spread_message()


def test_notification_enum_names_match_postgres():
    from app.infrastructure.database.models import NotificationType

    for member in (
        NotificationType.CARD_OF_DAY,
        NotificationType.SPREAD_SECOND,
        NotificationType.FREE_LIMIT_HIT,
    ):
        assert member.name == member.name.upper()
        assert member.name != member.value
