"""Sun-sign compatibility matrix and template texts."""

from __future__ import annotations

# score -1 tense, 0 neutral, 1 harmonious, 2 very harmonious
SUN_COMPAT: dict[tuple[str, str], int] = {}

SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы",
]

ELEMENT = {
    "Овен": "fire", "Лев": "fire", "Стрелец": "fire",
    "Телец": "earth", "Дева": "earth", "Козерог": "earth",
    "Близнецы": "air", "Весы": "air", "Водолей": "air",
    "Рак": "water", "Скорпион": "water", "Рыбы": "water",
}

def _init_matrix():
    if SUN_COMPAT:
        return
    for i, a in enumerate(SIGNS):
        for j, b in enumerate(SIGNS):
            if a == b:
                SUN_COMPAT[(a, b)] = 2
                continue
            ea, eb = ELEMENT[a], ELEMENT[b]
            if ea == eb:
                SUN_COMPAT[(a, b)] = 2
            elif (ea == "fire" and eb == "air") or (ea == "air" and eb == "fire"):
                SUN_COMPAT[(a, b)] = 1
            elif (ea == "earth" and eb == "water") or (ea == "water" and eb == "earth"):
                SUN_COMPAT[(a, b)] = 1
            elif (ea == "fire" and eb == "water") or (ea == "water" and eb == "fire"):
                SUN_COMPAT[(a, b)] = -1
            elif (ea == "earth" and eb == "air") or (ea == "air" and eb == "earth"):
                SUN_COMPAT[(a, b)] = -1
            else:
                SUN_COMPAT[(a, b)] = 0

_init_matrix()


LOVE_TEXT = {
    2: "Сильное притяжение: вы понимаете ритм друг друга и легко зажигаете общую искру.",
    1: "Хорошая совместимость: есть потенциал для тёплого и живого союза.",
    0: "Разные темпераменты, но именно контраст может сделать связь интересной.",
    -1: "Страсть и напряжение идут рядом — важно учиться слышать друг друга.",
}

FRIEND_TEXT = {
    2: "Лёгкая дружба: общие интересы и естественное взаимопонимание.",
    1: "Вы дополняете друг друга в разговорах и совместных делах.",
    0: "Дружба возможна, если уважать различия взглядов.",
    -1: "Дружба потребует терпения — зато научит видеть мир шире.",
}

CHALLENGE_TEXT = {
    2: "Риск — привыкнуть к комфорту и перестать развиваться.",
    1: "Иногда не хватает глубины — стоит честно проговаривать ожидания.",
    0: "Разный ритм жизни может создавать недопонимание.",
    -1: "Сильные эмоции и принципиальность — главный вызов пары.",
}

ADVICE_TEXT = {
    2: "Цените гармонию, но не забывайте о личном пространстве каждого.",
    1: "Развивайте общие цели — они скрепят вашу связь.",
    0: "Ищите точки соприкосновения через общие увлечения.",
    -1: "Пауза перед спором и юмор спасают даже сложные моменты.",
}


def sun_score(sign_a: str, sign_b: str) -> int:
    return SUN_COMPAT.get((sign_a, sign_b), 0)


def moon_bonus(sign_a: str | None, sign_b: str | None) -> int:
    if not sign_a or not sign_b:
        return 0
    if sign_a == sign_b:
        return 15
    ea, eb = ELEMENT.get(sign_a), ELEMENT.get(sign_b)
    if ea == eb:
        return 10
    if (ea == "water" and eb == "earth") or (ea == "earth" and eb == "water"):
        return 8
    return 0


def compatibility_score(sun_s: int, moon_bonus_pts: int) -> int:
    base = {2: 82, 1: 68, 0: 55, -1: 42}[sun_s]
    return min(98, max(30, base + moon_bonus_pts))
