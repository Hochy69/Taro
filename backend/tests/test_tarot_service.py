import pytest
from datetime import date

from app.application.services.tarot_ai_service import calculate_age, get_zodiac_sign


def test_calculate_age():
    birth = date(1990, 6, 15)
    age = calculate_age(birth)
    assert age >= 35


def test_get_zodiac_sign():
    assert get_zodiac_sign(date(1990, 3, 25)) == "Овен"
    assert get_zodiac_sign(date(1990, 1, 10)) == "Козерог"
    assert get_zodiac_sign(date(1990, 2, 20)) == "Рыбы"


def test_zodiac_boundaries():
    assert get_zodiac_sign(date(2000, 7, 22)) == "Рак"
    assert get_zodiac_sign(date(2000, 7, 23)) == "Лев"
