from app.application.services.channel_subscription_service import (
    required_channel_url,
    required_channel_username,
)


def test_required_channel_defaults():
    username = required_channel_username()
    assert username == "best1taro"
    assert required_channel_url() == "https://t.me/best1taro"
