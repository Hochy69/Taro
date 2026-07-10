from app.application.services.channel_subscription_service import (
    TEST_TELEGRAM_IDS,
    required_channel_url,
    required_channel_username,
)
from app.core.config import settings


def test_required_channel_defaults():
    username = required_channel_username()
    assert username == "best1taro"
    assert required_channel_url() == "https://t.me/best1taro"


def test_channel_subscribe_not_required_by_default():
    assert settings.telegram_channel_subscribe_required is False


def test_qa_telegram_ids_include_integration_user():
    assert 999999001 in TEST_TELEGRAM_IDS
    assert 555000111 in TEST_TELEGRAM_IDS
    assert 900000001 in TEST_TELEGRAM_IDS
