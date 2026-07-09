"""Check Telegram channel membership via Bot API."""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_SUBSCRIBED_STATUSES = frozenset({"creator", "administrator", "member", "restricted"})


def required_channel_username() -> str | None:
    raw = (settings.telegram_required_channel or "").strip()
    if not raw:
        return None
    if raw.startswith("https://t.me/"):
        raw = raw.rsplit("/", 1)[-1]
    return raw.lstrip("@")


def required_channel_url() -> str | None:
    username = required_channel_username()
    if not username:
        return None
    return f"https://t.me/{username}"


async def is_user_subscribed_to_required_channel(telegram_id: int) -> bool:
    username = required_channel_username()
    if not username:
        return True
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN missing — cannot verify channel subscription")
        return False

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/getChatMember"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                params={"chat_id": f"@{username}", "user_id": telegram_id},
            )
    except httpx.HTTPError as exc:
        logger.warning("getChatMember HTTP error telegram_id=%s: %s", telegram_id, exc)
        return False

    if response.status_code != 200:
        logger.warning(
            "getChatMember failed telegram_id=%s status=%s body=%s",
            telegram_id,
            response.status_code,
            response.text[:300],
        )
        return False

    payload = response.json()
    if not payload.get("ok"):
        logger.warning("getChatMember not ok: %s", payload)
        return False

    status = (payload.get("result") or {}).get("status")
    return status in _SUBSCRIBED_STATUSES
