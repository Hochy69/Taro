"""Synastry lite: compare two birth charts with templates."""

from __future__ import annotations

from datetime import date

from app.application.services.compatibility_templates import (
    ADVICE_TEXT,
    CHALLENGE_TEXT,
    FRIEND_TEXT,
    LOVE_TEXT,
    compatibility_score,
    moon_bonus,
    sun_score,
)
from app.application.services.ephemeris_service import compute_chart


def build_compatibility(
    user_name: str,
    user_birth_date: date,
    user_birth_time: str | None,
    user_birth_city: str | None,
    partner_name: str,
    partner_birth_date: date,
    partner_birth_time: str | None,
    partner_birth_city: str | None,
) -> dict:
    user_chart = compute_chart(user_birth_date, user_birth_time, user_birth_city)
    partner_chart = compute_chart(partner_birth_date, partner_birth_time, partner_birth_city)

    user_sun = next(p for p in user_chart["planets"] if p["key"] == "sun")
    user_moon = next(p for p in user_chart["planets"] if p["key"] == "moon")
    partner_sun = next(p for p in partner_chart["planets"] if p["key"] == "sun")
    partner_moon = next(p for p in partner_chart["planets"] if p["key"] == "moon")

    sun_s = sun_score(user_sun["sign"], partner_sun["sign"])
    moon_pts = moon_bonus(user_moon["sign"], partner_moon["sign"])
    score = compatibility_score(sun_s, moon_pts)

    summary = (
        f"{user_name} ({user_sun['sign']}) и {partner_name} ({partner_sun['sign']}): "
        f"совместимость {score}% по солнцу и луне."
    )

    moon_match = None
    if user_moon["sign"] and partner_moon["sign"]:
        if user_moon["sign"] == partner_moon["sign"]:
            moon_match = f"Луны в {user_moon['sign']} — эмоциональный язык похож, вы чувствуете друг друга тоньше."
        elif moon_bonus(user_moon["sign"], partner_moon["sign"]) >= 8:
            moon_match = f"Луна {user_name} в {user_moon['sign']} и Луна {partner_name} в {partner_moon['sign']} поддерживают друг друга."
        else:
            moon_match = f"Луны в {user_moon['sign']} и {partner_moon['sign']} — разные эмоциональные ритмы, нужна бережность."

    love = LOVE_TEXT[sun_s]
    friendship = FRIEND_TEXT[sun_s]
    challenges = CHALLENGE_TEXT[sun_s]
    advice = ADVICE_TEXT[sun_s]

    text = "\n\n".join([
        summary,
        f"☉ Солнце: {user_sun['sign']} + {partner_sun['sign']} — {love}",
        moon_match or "",
        f"💫 Вызовы: {challenges}",
        f"✨ Совет: {advice}",
    ])

    return {
        "partner_name": partner_name,
        "score": score,
        "summary": summary,
        "user_sun_sign": user_sun["sign"],
        "partner_sun_sign": partner_sun["sign"],
        "user_moon_sign": user_moon["sign"],
        "partner_moon_sign": partner_moon["sign"],
        "sun_match": f"Солнце {user_sun['sign']} и {partner_sun['sign']}: {love}",
        "moon_match": moon_match,
        "love": love,
        "friendship": friendship,
        "challenges": challenges,
        "advice": advice,
        "text": text,
    }
