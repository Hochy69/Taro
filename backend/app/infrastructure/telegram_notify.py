"""Send Telegram bot messages from backend workers (Celery)."""

from __future__ import annotations

import html
import logging
import re

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")


def escape_telegram_html(text: str) -> str:
    return html.escape(text, quote=False)


async def send_telegram_message(
    telegram_id: int,
    text: str,
    *,
    parse_mode: str | None = "HTML",
    reply_markup: dict | None = None,
) -> bool:
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not configured — cannot send notification")
        return False

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload: dict[str, object] = {
        "chat_id": telegram_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, json=payload)
    except httpx.HTTPError as exc:
        logger.warning("Telegram send HTTP error chat_id=%s: %s", telegram_id, exc)
        return False

    if response.status_code == 200:
        return True

    logger.warning(
        "Telegram send failed chat_id=%s status=%s body=%s",
        telegram_id,
        response.status_code,
        response.text[:500],
    )

    if parse_mode:
        plain = html.unescape(_TAG_RE.sub("", text)).strip()
        if plain and plain != text:
            return await send_telegram_message(
                telegram_id,
                plain,
                parse_mode=None,
                reply_markup=reply_markup,
            )
    return False


def web_app_button(text: str, url: str) -> dict:
    return {"text": text, "web_app": {"url": url}}


def web_app_keyboard(*buttons: dict) -> dict:
    return {"inline_keyboard": [list(buttons)]}
