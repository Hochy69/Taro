"""Build natal chart API response from ephemeris + templates."""

from __future__ import annotations

from datetime import date

from app.application.services.ephemeris_service import compute_chart
from app.application.services.natal_templates import chart_summary, planet_interpretation


def build_natal_chart(
    name: str,
    birth_date: date,
    birth_time: str | None,
    birth_city: str | None,
) -> dict:
    chart = compute_chart(birth_date, birth_time, birth_city)

    planets_out = []
    for p in chart["planets"]:
        planets_out.append({
            **p,
            "interpretation": planet_interpretation(p["name"], p["sign"], p.get("house")),
            "wheel_angle": p["longitude"],
        })

    aspects = _major_aspects(chart["planets"])

    return {
        "birth_date": chart["birth_date"],
        "birth_time": chart["birth_time"],
        "birth_city": chart["birth_city"],
        "time_unknown": chart["time_unknown"],
        "ascendant": chart["ascendant"],
        "ascendant_emoji": chart["ascendant_emoji"],
        "ascendant_degree": chart["ascendant_degree"],
        "ascendant_longitude": chart.get("ascendant_longitude"),
        "summary": chart_summary(name, chart),
        "planets": planets_out,
        "houses": chart["houses"],
        "aspects": aspects,
        "text": _full_text(name, planets_out, chart, aspects),
    }


def _aspect_angle(a: float, b: float) -> float:
    diff = abs(a - b) % 360
    return diff if diff <= 180 else 360 - diff


def _major_aspects(planets: list[dict]) -> list[dict]:
    names = {
        0: "соединение", 60: "секстиль", 90: "квадрат", 120: "трин", 180: "оппозиция",
    }
    orbs = {0: 8, 60: 6, 90: 7, 120: 7, 180: 8}
    result = []
    for i, a in enumerate(planets):
        for b in planets[i + 1:]:
            angle = _aspect_angle(a["longitude"], b["longitude"])
            for asp_angle, orb in orbs.items():
                if abs(angle - asp_angle) <= orb:
                    result.append({
                        "planet_a": a["name"],
                        "planet_b": b["name"],
                        "aspect": names[asp_angle],
                        "angle": round(angle, 1),
                        "description": _aspect_text(a["name"], b["name"], names[asp_angle]),
                    })
                    break
    return result[:8]


def _aspect_text(a: str, b: str, aspect: str) -> str:
    templates = {
        "соединение": f"{a} и {b} сливаются — их темы усиливают друг друга.",
        "секстиль": f"{a} и {b} в гармонии — есть лёгкая поддержка между ними.",
        "квадрат": f"{a} и {b} создают напряжение — через него растёт осознанность.",
        "трин": f"{a} и {b} текут естественно — таланты здесь даются легче.",
        "оппозиция": f"{a} и {b} учат балансу — важно интегрировать оба полюса.",
    }
    return templates.get(aspect, f"{a} и {b} связаны аспектом {aspect}.")


def _full_text(name: str, planets: list[dict], chart: dict, aspects: list[dict]) -> str:
    lines = [chart_summary(name, chart), ""]
    for p in planets[:5]:
        lines.append(f"{p['symbol']} {p['name']} в {p['sign']} ({p['degree']}°): {p['interpretation']}")
    if aspects:
        lines.append("")
        lines.append("Ключевые аспекты:")
        for asp in aspects[:3]:
            lines.append(f"• {asp['description']}")
    return "\n".join(lines)
