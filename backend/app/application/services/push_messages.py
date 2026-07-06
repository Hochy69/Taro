"""Marketing push copy for Telegram bot notifications."""

from __future__ import annotations

from app.core.config import settings
from app.infrastructure.telegram_notify import web_app_button, web_app_keyboard


def _webapp() -> str:
    return settings.telegram_webapp_url.rstrip("/")


def start_no_webapp_keyboard() -> dict:
    return web_app_keyboard(web_app_button("🔮 Открыть расклад", _webapp()))


def start_no_webapp_message() -> str:
    return (
        "✨ <b>Вы на шаге от первого расклада</b>\n\n"
        "Нажмите «🔮 Открыть расклад» — 3 бесплатные попытки уже ждут.\n\n"
        "Любовь, деньги, карьера — выберите, что волнует сейчас."
    )


def after_first_spread_message() -> str:
    return (
        "🔮 <b>Как вам первый расклад?</b>\n\n"
        "Если тема отношений — загляните в «💕 Что между вами»:\n"
        "совместимость по датам рождения покажет сильные стороны пары и зоны напряжения.\n\n"
        "Осталось бесплатных раскладов: 2 из 3."
    )


def after_second_spread_message() -> str:
    return (
        "💫 <b>Остался 1 бесплатный расклад</b>\n\n"
        "Хорошие темы на последний бесплатный:\n"
        "• Любовь — если есть вопрос к человеку\n"
        "• Предназначение — если чувствуете развилку\n"
        "• Общий — если всё смешалось в голове\n\n"
        "Откройте приложение — кнопка «Открыть расклад» внизу чата."
    )


def after_third_spread_message() -> str:
    return free_limit_exhausted_message()


def free_limit_exhausted_message() -> str:
    p = settings
    return (
        "✨ <b>Вы использовали 3 бесплатных расклада</b>\n\n"
        f"Следующие бесплатные — через {p.free_spread_period_days} дня.\n\n"
        "Хотите сейчас?\n"
        f"• 🃏 Разовый расклад — {p.price_single_spread} ⭐\n"
        f"• 💕 «Что между вами» — проверка пары\n"
        "• ⭐️ Premium — совместимость бесплатно + 15 раскладов в день\n\n"
        "Откройте приложение 👇"
    )


def limit_followup_message(days_until_free: int) -> str:
    p = settings
    return (
        "🌙 <b>Вчера карты что-то подсказали?</b>\n\n"
        f"Если вопрос не отпустил — можно сделать ещё один расклад за {p.price_single_spread} ⭐\n"
        "или проверить пару в «Что между вами».\n\n"
        f"Напоминаем: через {days_until_free} дн. снова будут бесплатные расклады."
    )


def daily_card_push_intro() -> str:
    return (
        "🃏 <b>Ваша карта дня готова</b>\n\n"
        "Откройте приложение — послание дня + совет карт.\n"
        "А если день про отношения — загляните в «Что между вами» 💕"
    )


def compat_abandon_message() -> str:
    return (
        "💕 <b>Проверка пары почти готова</b>\n\n"
        "Вы уже на экране «Что между вами» — осталось оплатить проверку "
        "и ввести данные партнёра.\n\n"
        "Узнайте до разговора, который всё может изменить."
    )


def compat_paid_upsell_message() -> str:
    return (
        "✅ <b>Совместимость готова — смотрите результат в приложении</b>\n\n"
        "Хотите глубже? Пакет «Любовь»: совместимость + расклад на отношения "
        "выгоднее, чем по отдельности.\n\n"
        "Откройте Premium →"
    )


def weekly_referral_message() -> str:
    return (
        "🎁 <b>Пригласите друга — расклад вам обоим</b>\n\n"
        "Отправьте ссылку из раздела «Пригласить друга».\n"
        "Когда подруга зайдёт в бота — вы оба получите бонус.\n\n"
        "Команда: /invite"
    )


def spread_keyboard() -> dict:
    return web_app_keyboard(web_app_button("🔮 Открыть расклад", _webapp()))


def compat_keyboard() -> dict:
    return web_app_keyboard(
        web_app_button("💕 Что между вами", f"{_webapp()}/compatibility"),
    )


def app_keyboard() -> dict:
    return web_app_keyboard(web_app_button("🔮 Открыть приложение", _webapp()))


def premium_keyboard() -> dict:
    return web_app_keyboard(
        web_app_button("⭐️ Premium", f"{_webapp()}/subscription"),
    )
