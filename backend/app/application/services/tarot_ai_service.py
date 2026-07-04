import logging
import re
import time
from datetime import date

from app.application.services.reading_templates import (
    PSYCHOLOGICAL_SYSTEM_PROMPT,
    render_fallback,
)
from app.core.config import settings
from app.infrastructure.ai.providers import AIResponse, get_ai_provider

logger = logging.getLogger(__name__)

# Единый психологический шаблон-промпт для всех раскладов.
SYSTEM_PROMPT = PSYCHOLOGICAL_SYSTEM_PROMPT


def calculate_age(birth_date: date) -> int:
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def get_zodiac_sign(birth_date: date) -> str:
    day, month = birth_date.day, birth_date.month
    signs = [
        (1, 20, "Козерог", "Водолей"),
        (2, 19, "Водолей", "Рыбы"),
        (3, 20, "Рыбы", "Овен"),
        (4, 20, "Овен", "Телец"),
        (5, 21, "Телец", "Близнецы"),
        (6, 21, "Близнецы", "Рак"),
        (7, 22, "Рак", "Лев"),
        (8, 23, "Лев", "Дева"),
        (9, 23, "Дева", "Весы"),
        (10, 23, "Весы", "Скорпион"),
        (11, 22, "Скорпион", "Стрелец"),
        (12, 22, "Стрелец", "Козерог"),
    ]
    for m, d, before, after in signs:
        if month == m:
            return before if day <= d else after
    return "Козерог"


def _parse_sections(text: str) -> dict[str, str]:
    sections = {
        "past": "",
        "present": "",
        "future": "",
        "advice": "",
        "conclusion": "",
    }
    patterns = {
        "past": r"##\s*Карта прошлого\s*\n(.*?)(?=##|\Z)",
        "present": r"##\s*Карта настоящего\s*\n(.*?)(?=##|\Z)",
        "future": r"##\s*Карта будущего\s*\n(.*?)(?=##|\Z)",
        "advice": r"##\s*Совет карт\s*\n(.*?)(?=##|\Z)",
        "conclusion": r"##\s*Главный вывод\s*\n(.*?)(?=##|\Z)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            sections[key] = match.group(1).strip()
    return sections


def _is_usable(sections: dict[str, str]) -> bool:
    """Ответ считается пригодным, если разобрались основные смысловые секции."""
    core = [sections.get("present"), sections.get("future"), sections.get("conclusion")]
    return any(bool(s and s.strip()) for s in core)


class TarotAIService:
    async def generate_reading(
        self,
        name: str,
        birth_date: date | None,
        zodiac_sign: str | None,
        category: str,
        situation: str,
        emotion: str,
        cards: list[dict],
        category_slug: str | None = None,
    ) -> AIResponse:
        age = calculate_age(birth_date) if birth_date else None
        zodiac = zodiac_sign or (get_zodiac_sign(birth_date) if birth_date else "не указан")

        cards_text = "\n".join(
            f"- {c['position']}: {c['name']}"
            f"{' (перевёрнутая)' if c.get('is_reversed') else ''}"
            f"\n  Значение: {c['meaning']}"
            for c in cards
        )

        user_prompt = f"""Клиент: {name}
Возраст: {age or 'не указан'}
Знак зодиака: {zodiac}
Сфера: {category}
Ситуация: {situation}
Эмоция: {emotion}

Выпавшие карты:
{cards_text}

Создай персональный поддерживающий расклад с психологическим уклоном: признай
чувства клиента, покажи смысл прошлого, честно назови трудность настоящего и
обязательно разверни к надежде — «сейчас тяжело, но станет лучше». Объедини
значения карт в единый связный рассказ. Каждый расклад должен звучать по-новому:
варьируй формулировки, не повторяй одни и те же обороты из прошлых ответов."""

        start = time.monotonic()
        if settings.template_only:
            fb = render_fallback(
                name=name,
                category=category,
                situation=situation,
                emotion=emotion,
                cards=cards,
                slug=category_slug,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return AIResponse(
                text=fb["text"],
                past=fb["past"],
                present=fb["present"],
                future=fb["future"],
                advice=fb["advice"],
                conclusion=fb["conclusion"],
                prompt_tokens=0,
                completion_tokens=0,
                generation_time_ms=elapsed_ms,
            )

        try:
            provider = get_ai_provider()
            text, prompt_tokens, completion_tokens = await provider.generate(
                SYSTEM_PROMPT, user_prompt
            )
            sections = _parse_sections(text)

            # Если модель не вернула осмысленный структурированный ответ —
            # используем локальный психологический шаблон.
            if not text.strip() or not _is_usable(sections):
                raise ValueError("AI response is empty or unstructured")

            elapsed_ms = int((time.monotonic() - start) * 1000)
            return AIResponse(
                text=text,
                past=sections["past"],
                present=sections["present"],
                future=sections["future"],
                advice=sections["advice"],
                conclusion=sections["conclusion"],
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                generation_time_ms=elapsed_ms,
            )
        except Exception as e:
            logger.warning("AI provider unavailable, using template fallback: %s", e)
            fb = render_fallback(
                name=name,
                category=category,
                situation=situation,
                emotion=emotion,
                cards=cards,
                slug=category_slug,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return AIResponse(
                text=fb["text"],
                past=fb["past"],
                present=fb["present"],
                future=fb["future"],
                advice=fb["advice"],
                conclusion=fb["conclusion"],
                prompt_tokens=0,
                completion_tokens=0,
                generation_time_ms=elapsed_ms,
            )
