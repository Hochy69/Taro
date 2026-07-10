from app.application.services.channel_subscription_service import (
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
