import logging

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    WebAppInfo,
)

from app.config import settings
from app.webapp_url import get_webapp_url

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()


async def _webapp_is_reachable(url: str) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=8.0, follow_redirects=True)
            return resp.status_code < 500
    except Exception as e:  # noqa: BLE001
        logging.warning("WebApp URL check failed (%s): %s", url, e)
        return False


def _unreachable_note() -> str:
    return (
        "\n\n<i>Если кнопка не открывается — отправьте /start ещё раз "
        "через минуту.</i>"
    )


def webapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔮 Открыть расклад",
                    web_app=WebAppInfo(url=get_webapp_url()),
                )
            ]
        ]
    )


@dp.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    name = message.from_user.first_name or "друг"
    webapp_url = get_webapp_url()

    if command.args and command.args.lower().startswith("ref_"):
        await _save_pending_referral(message.from_user.id, command.args)

    reachable = await _webapp_is_reachable(webapp_url)
    if not reachable:
        logging.warning("WebApp URL not reachable from bot, showing button anyway: %s", webapp_url)

    referral_note = ""
    if command.args and command.args.lower().startswith("ref_"):
        referral_note = (
            "\n\n🎁 <b>Друг пригласил вас!</b> После регистрации вы оба получите "
            "бесплатный расклад в подарок."
        )

    await message.answer(
        f"✨ <b>Добро пожаловать, {name}!</b>\n\n"
        "Я — ваш проводник в Мир Таро. Карты готовы раскрыть тайны "
        "любви, карьеры, финансов и предназначения."
        f"{referral_note}\n\n"
        "Нажмите кнопку ниже, чтобы начать расклад 👇"
        f"{'' if reachable else _unreachable_note()}",
        reply_markup=webapp_keyboard(),
        parse_mode="HTML",
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🔮 <b>Мир Таро — команды</b>\n\n"
        "• /start — приветствие и расклад\n"
        "• /app — открыть мини-приложение\n"
        "• /premium — подписка и разовые расклады\n"
        "• /invite — пригласить друга (бонусный расклад)\n"
        "• /history — история ваших раскладов\n"
        "• /help — эта справка\n\n"
        "Нажмите «Меню» слева от поля ввода, чтобы увидеть все команды.",
        reply_markup=webapp_keyboard(),
        parse_mode="HTML",
    )


@dp.message(Command("app"))
async def cmd_app(message: Message):
    webapp_url = get_webapp_url()
    reachable = await _webapp_is_reachable(webapp_url)
    await message.answer(
        "🔮 Нажмите кнопку ниже, чтобы открыть Мир Таро:"
        f"{'' if reachable else _unreachable_note()}",
        reply_markup=webapp_keyboard(),
        parse_mode="HTML",
    )


@dp.message(Command("history"))
async def cmd_history(message: Message):
    await message.answer(
        "📜 <b>История раскладов</b>\n\n"
        "Все ваши прошлые расклады доступны в мини-приложении.",
        reply_markup=webapp_keyboard(),
        parse_mode="HTML",
    )


@dp.message(Command("invite"))
async def cmd_invite(message: Message):
    await message.answer(
        "🎁 <b>Пригласи друга</b>\n\n"
        "За каждого друга, который впервые зарегистрируется по вашей ссылке, "
        "вы оба получите бесплатный расклад в подарок.\n\n"
        "Откройте приложение — ссылка для приглашения в разделе Premium.",
        reply_markup=webapp_keyboard(),
        parse_mode="HTML",
    )


@dp.message(Command("premium"))
async def cmd_premium(message: Message):
    await message.answer(
        "⭐️ <b>Premium подписка</b>\n\n"
        "📅 1 месяц — 450 ⭐️\n"
        "📅 3 месяца — 1200 ⭐️\n"
        "📅 6 месяцев — 2100 ⭐️\n\n"
        "• 15 раскладов в сутки\n"
        "• Полная история\n"
        "• Все функции\n\n"
        "Оформите подписку в приложении 👇",
        reply_markup=webapp_keyboard(),
        parse_mode="HTML",
    )


@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Hidden admin activation: `/admin <secret word>`.

    Regular users never learn this exists: any call without the correct
    secret word is silently ignored (no reply), just like any other
    unrecognized message.
    """
    parts = (message.text or "").split(maxsplit=1)
    word = parts[1].strip() if len(parts) > 1 else ""
    if not word:
        return

    result = await _grant_admin_on_backend(message.from_user, word)
    if not result or not result.get("granted"):
        # Wrong word — stay hidden, behave as if the command doesn't exist.
        return

    admin_url = result.get("admin_url")
    await message.answer(
        "✅ <b>Доступ администратора активирован навсегда.</b>\n\n"
        "Теперь у вас безлимитные расклады и полный доступ ко всем функциям.\n\n"
        f"🔐 Админ-панель: {admin_url}",
        reply_markup=webapp_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


async def _grant_admin_on_backend(tg_user, word: str) -> dict | None:
    import httpx

    url = f"{settings.api_url.rstrip('/')}/api/v1/admin/grant"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json={
                    "internal_secret": settings.internal_api_secret,
                    "word": word,
                    "telegram_id": tg_user.id,
                    "username": tg_user.username,
                    "first_name": tg_user.first_name,
                },
                timeout=15.0,
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:  # noqa: BLE001
        logging.warning("Failed to grant admin on backend: %s", e)
    return None


async def _save_pending_referral(telegram_id: int, referral_payload: str) -> None:
    import httpx

    url = f"{settings.api_url.rstrip('/')}/api/v1/referral/pending"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                url,
                json={
                    "telegram_id": telegram_id,
                    "referral_code": referral_payload,
                    "secret": settings.internal_api_secret,
                },
                timeout=15.0,
            )
    except Exception as e:  # noqa: BLE001
        logging.warning("Failed to save pending referral: %s", e)


@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    payment = message.successful_payment

    # Activate the purchase on the backend (payload carries our payment id).
    confirmed = await _confirm_payment_on_backend(
        payload=payment.invoice_payload,
        charge_id=payment.telegram_payment_charge_id,
    )

    if confirmed:
        text = (
            f"✅ Оплата получена! ({payment.total_amount} ⭐️)\n"
            "Ваш доступ активирован. Приятного расклада!"
        )
    else:
        text = (
            f"✅ Оплата получена! ({payment.total_amount} ⭐️)\n"
            "Доступ активируется в течение минуты. Если что-то не так — напишите нам."
        )

    await message.answer(text, reply_markup=webapp_keyboard())


async def _confirm_payment_on_backend(payload: str | None, charge_id: str | None) -> bool:
    if not payload:
        return False
    import httpx

    url = f"{settings.api_url.rstrip('/')}/api/v1/payments/telegram/confirm"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json={
                    "payload": payload,
                    "telegram_payment_charge_id": charge_id or "",
                    "secret": settings.internal_api_secret,
                },
                timeout=15.0,
            )
            return resp.status_code == 200
    except Exception as e:  # noqa: BLE001
        logging.warning("Failed to confirm payment on backend: %s", e)
        return False


@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


async def send_invoice(
    chat_id: int,
    title: str,
    description: str,
    stars: int,
    payload: str,
):
    await bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=stars)],
        provider_token="",
    )
