"""Planet positions and ascendant (PyEphem, template-friendly MVP)."""

from __future__ import annotations

import math
from datetime import date, datetime, time

import ephem

from app.application.services.geocoding_service import resolve_city
from app.application.services.tarot_ai_service import get_zodiac_sign

ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы",
]

SIGN_EMOJI = {
    "Овен": "♈", "Телец": "♉", "Близнецы": "♊", "Рак": "♋",
    "Лев": "♌", "Дева": "♍", "Весы": "♎", "Скорпион": "♏",
    "Стрелец": "♐", "Козерог": "♑", "Водолей": "♒", "Рыбы": "♓",
}

PLANETS = [
    ("sun", "Солнце", "☉", ephem.Sun),
    ("moon", "Луна", "☽", ephem.Moon),
    ("mercury", "Меркурий", "☿", ephem.Mercury),
    ("venus", "Венера", "♀", ephem.Venus),
    ("mars", "Марс", "♂", ephem.Mars),
    ("jupiter", "Юпитер", "♃", ephem.Jupiter),
    ("saturn", "Сатурн", "♄", ephem.Saturn),
]


def _parse_birth_time(birth_time: str | None) -> time | None:
    if not birth_time or birth_time.strip().lower() in {"", "unknown", "не знаю"}:
        return None
    parts = birth_time.strip().split(":")
    try:
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        if 0 <= h <= 23 and 0 <= m <= 59:
            return time(h, m)
    except (ValueError, IndexError):
        pass
    return None



def _ecliptic_longitude(body, observer: ephem.Observer) -> float:
    body.compute(observer)
    ecl = ephem.Ecliptic(body)
    return math.degrees(ecl.lon) % 360


def longitude_to_sign(longitude: float) -> tuple[str, float]:
    idx = int(longitude // 30) % 12
    return ZODIAC_SIGNS[idx], round(longitude % 30, 1)


OBLIQUITY = math.radians(23.4392911)


def _ascendant_longitude(observer: ephem.Observer) -> float | None:
    try:
        sidereal = observer.sidereal_time()
        lat = float(observer.lat)
        asc = math.degrees(
            math.atan2(
                math.cos(sidereal),
                -math.sin(sidereal) * math.cos(OBLIQUITY) - math.tan(lat) * math.sin(OBLIQUITY),
            )
        )
        return asc % 360
    except Exception:
        return None


def _equal_house(house_num: int, asc_lon: float) -> tuple[str, float]:
    lon = (asc_lon + (house_num - 1) * 30) % 360
    return longitude_to_sign(lon)


def _planet_house(planet_lon: float, asc_lon: float) -> int:
    diff = (planet_lon - asc_lon) % 360
    return int(diff // 30) + 1


def _utc_datetime(birth_date: date, birth_time: time | None, utc_offset: int) -> datetime:
    if birth_time:
        local = datetime.combine(birth_date, birth_time)
    else:
        local = datetime.combine(birth_date, time(12, 0))
    return local - __import__("datetime").timedelta(hours=utc_offset)


def compute_chart(
    birth_date: date,
    birth_time: str | None,
    birth_city: str | None,
) -> dict:
    lat, lon, utc_offset, city_label = resolve_city(birth_city)
    bt = _parse_birth_time(birth_time)
    utc_dt = _utc_datetime(birth_date, bt, utc_offset)

    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = utc_dt.strftime("%Y/%m/%d %H:%M:%S")

    asc_lon = _ascendant_longitude(observer) if bt else None
    asc_sign, asc_degree = longitude_to_sign(asc_lon) if asc_lon is not None else (None, None)

    planets: list[dict] = []
    for key, label, symbol, factory in PLANETS:
        body = factory()
        body.compute(observer)
        ecl = ephem.Ecliptic(body)
        lon = math.degrees(ecl.lon) % 360
        sign, degree = longitude_to_sign(lon)
        house = _planet_house(lon, asc_lon) if asc_lon is not None else None
        planets.append({
            "key": key,
            "name": label,
            "symbol": symbol,
            "sign": sign,
            "sign_emoji": SIGN_EMOJI[sign],
            "degree": degree,
            "longitude": round(lon, 2),
            "house": house,
        })

    houses: list[dict] = []
    if asc_lon is not None:
        for n in range(1, 13):
            sign, degree = _equal_house(n, asc_lon)
            houses.append({"house": n, "sign": sign, "sign_emoji": SIGN_EMOJI[sign], "degree": degree})

    return {
        "birth_date": birth_date.isoformat(),
        "birth_time": birth_time if bt else None,
        "birth_city": city_label,
        "latitude": lat,
        "longitude": lon,
        "utc_offset": utc_offset,
        "time_unknown": bt is None,
        "ascendant": asc_sign,
        "ascendant_emoji": SIGN_EMOJI.get(asc_sign) if asc_sign else None,
        "ascendant_degree": asc_degree,
        "ascendant_longitude": round(asc_lon, 2) if asc_lon is not None else None,
        "sun_sign": get_zodiac_sign(birth_date),
        "planets": planets,
        "houses": houses,
    }
