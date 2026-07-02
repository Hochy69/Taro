"""Prepare Telegram share messages for Mini App shareMessage()."""

from __future__ import annotations

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.infrastructure.database.models import Spread, SpreadCard, User


def build_spread_share_text(spread: Spread) -> str:
    ordered = sorted(spread.cards, key=lambda sc: sc.order)
    cards = " • ".join(
        f"{sc.card.name}{' (перев.)' if sc.is_reversed else ''}" for sc in ordered
    )
    category = spread.category.name if spread.category else ""
    ai = spread.ai_result

    lines = ["🔮 Мой расклад в Мире Таро"]
    if category:
        lines.append(f"Тема: {category}")
    if cards:
        lines.append(f"Карты: {cards}")
    lines.append("")

    if ai:
        if ai.conclusion:
            lines.extend(["✨ Главный вывод", ai.conclusion, ""])
        if ai.advice:
            lines.extend(["💫 Совет карт", ai.advice])

    return "\n".join(lines).strip()[:3900]


async def prepare_spread_share_message(session: AsyncSession, spread_id: int, user: User) -> str:
    result = await session.execute(
        select(Spread)
        .options(
            selectinload(Spread.cards).selectinload(SpreadCard.card),
            selectinload(Spread.category),
            selectinload(Spread.ai_result),
        )
        .where(Spread.id == spread_id, Spread.user_id == user.id)
    )
    spread = result.scalar_one_or_none()
    if not spread:
        raise ValueError("Spread not found")
    if not spread.ai_result:
        raise ValueError("Spread not interpreted yet")

    text = build_spread_share_text(spread)
    title = f"Расклад: {spread.category.name if spread.category else 'Таро'}"

    payload = {
        "user_id": user.telegram_id,
        "result": {
            "type": "article",
            "id": f"spread-{spread_id}",
            "title": title[:64],
            "description": text[:256].replace("\n", " "),
            "input_message_content": {
                "message_text": text,
            },
        },
        "allow_user_chats": True,
        "allow_bot_chats": False,
        "allow_group_chats": True,
        "allow_channel_chats": False,
    }

    token = settings.telegram_bot_token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.telegram.org/bot{token}/savePreparedInlineMessage",
            json=payload,
            timeout=15.0,
        )
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"savePreparedInlineMessage failed: {data}")
        return data["result"]["id"]
