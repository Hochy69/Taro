"""Deterministic card-of-the-day with template interpretation."""

import hashlib
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import TarotCard, TarotMeaning

_DAY_OPENERS = [
    "{name}, сегодня карта **{card}**{rev} приходит как зеркало дня.",
    "День открывается картой **{card}**{rev} — послание для {name}.",
    "Для {name} сегодня ключевая энергия — **{card}**{rev}.",
    "Карта дня **{card}**{rev} мягко направляет {name} через этот день.",
]

_DAY_ADVICE = [
    "Обратите внимание на ситуации, где проявится тема этой карты — там сегодня ваш главный урок.",
    "Не спешите с выводами: дайте карте дня проявиться к вечеру.",
    "Запишите одну мысль, которая придёт при чтении этой карты — она может оказаться важной.",
    "Сегодня лучше действовать в согласии с посланием карты, а не против него.",
]

_CONCLUSION = [
    "Пусть этот день принесёт ясность и спокойную уверенность.",
    "Карта дня — не приговор, а подсказка. Выбор всегда за вами.",
    "Примите послание с благодарностью — даже если оно требует честности с собой.",
]


def _daily_seed(user_id: int, day: date) -> int:
    raw = f"{user_id}:{day.isoformat()}"
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


def _pick(pool: list[str], seed: int, offset: int = 0) -> str:
    return pool[(seed + offset) % len(pool)]


async def get_card_of_day(
    session: AsyncSession,
    user_id: int,
    name: str,
    zodiac_sign: str | None,
    day: date | None = None,
) -> dict:
    today = day or date.today()
    seed = _daily_seed(user_id, today)

    result = await session.execute(select(TarotCard).order_by(TarotCard.id))
    cards = list(result.scalars().all())
    if not cards:
        raise ValueError("No cards in deck")

    card = cards[seed % len(cards)]
    is_reversed = (seed >> 4) % 3 == 0

    meaning_result = await session.execute(
        select(TarotMeaning).where(
            TarotMeaning.card_id == card.id,
            TarotMeaning.category_slug == "general",
            TarotMeaning.position.in_(["reversed" if is_reversed else "upright", "upright"]),
        )
    )
    meanings = meaning_result.scalars().all()
    meaning_text = meanings[0].meaning if meanings else "Карта несёт важное послание на сегодня."
    advice_text = meanings[0].advice if meanings and meanings[0].advice else _pick(_DAY_ADVICE, seed, 1)

    rev = " (перевёрнутая)" if is_reversed else ""
    opener = _pick(_DAY_OPENERS, seed).format(name=name, card=card.name, rev=rev)
    zodiac_line = f"Знак **{zodiac_sign}** добавляет личный оттенок этому посланию." if zodiac_sign else ""
    conclusion = _pick(_CONCLUSION, seed, 2)

    text = "\n\n".join(
        part for part in [opener, meaning_text, advice_text, zodiac_line, conclusion] if part
    )

    return {
        "date": today.isoformat(),
        "card": {
            "id": card.id,
            "slug": card.slug,
            "name": card.name,
            "is_reversed": is_reversed,
            "image_url": card.image_url,
        },
        "meaning": meaning_text,
        "advice": advice_text,
        "conclusion": conclusion,
        "text": text,
    }
