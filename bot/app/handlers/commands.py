import logging

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    CallbackQuery,
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

_SUBSCRIBED_STATUSES = frozenset({"creator", "administrator", "member", "restricted"})


def _required_channel_username() -> str | None:
    raw = (settings.telegram_required_channel or "").strip()
    if not raw:
        return None
    if raw.startswith("https://t.me/"):
        raw = raw.rsplit("/", 1)[-1]
    return raw.lstrip("@")


def _required_channel_url() -> str:
    username = _required_channel_username()
    return f"https://t.me/{username}" if username else "https://t.me/best1taro"


async def _is_channel_member(user_id: int) -> bool:
    username = _required_channel_username()
    if not username:
        return True
    try:
        member = await bot.get_chat_member(chat_id=f"@{username}", user_id=user_id)
        return member.status in _SUBSCRIBED_STATUSES
    except Exception as e:  # noqa: BLE001
        logging.warning("Channel membership check failed user_id=%s: %s", user_id, e)
        return False


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


def webapp_keyboard(url: str | None = None) -> InlineKeyboardMarkup:
    target = url or get_webapp_url()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔮 Открыть расклад",
                    web_app=WebAppInfo(url=target),
                )
            ]
        ]
    )


def start_keyboard(*, show_channel_invite: bool = False) -> InlineKeyboardMarkup:
    base = get_webapp_url().rstrip("/")
    rows = [
        [
            InlineKeyboardButton(
                text="🔮 Открыть расклад",
                web_app=WebAppInfo(url=base),
            )
        ],
        [
            InlineKeyboardButton(
                text="💕 Что между вами",
                web_app=WebAppInfo(url=f"{base}/compatibility"),
            )
        ],
    ]
    if show_channel_invite:
        rows.append(
            [InlineKeyboardButton(text="📢 Канал с картой дня", url=_required_channel_url())]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def compatibility_keyboard() -> InlineKeyboardMarkup:
    target = f"{get_webapp_url().rstrip('/')}/compatibility"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💕 Что между вами",
                    web_app=WebAppInfo(url=target),
                )
            ]
        ]
    )


@dp.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    if command.args and command.args.lower().startswith("ref_"):
        await _save_pending_referral(message.from_user.id, command.args)

    await _send_start_welcome(message, command)


@dp.callback_query(F.data == "check_channel_sub")
async def on_check_channel_sub(callback: CallbackQuery):
    if not callback.from_user or not callback.message:
        return

    if await _is_channel_member(callback.from_user.id):
        await callback.answer("Вы уже подписаны на канал. Спасибо!")
    else:
        await callback.answer(
            "Подписка пока не найдена. Это необязательно — можете пользоваться ботом.",
            show_alert=True,
        )


async def _send_start_welcome(
    message: Message,
    command: CommandObject | None,
    *,
    edit: bool = False,
    first_name: str | None = None,
):
    name = first_name or (message.from_user.first_name if message.from_user else None) or "друг"
    webapp_url = get_webapp_url()
    telegram_id = message.chat.id
    user_id = message.from_user.id if message.from_user else telegram_id

    await _schedule_start_reminder(telegram_id)

    reachable = await _webapp_is_reachable(webapp_url)
    if not reachable:
        logging.warning("WebApp URL not reachable from bot, showing button anyway: %s", webapp_url)

    referral_note = ""
    if command and command.args and command.args.lower().startswith("ref_"):
        referral_note = (
            "\n\n🎁 <b>Друг пригласил вас!</b> После регистрации вы оба получите "
            "бесплатный расклад в подарок."
        )

    channel_note = ""
    show_channel_invite = False
    if settings.telegram_required_channel and not settings.telegram_channel_subscribe_required:
        subscribed = await _is_channel_member(user_id)
        show_channel_invite = not subscribed
        if show_channel_invite:
            channel_note = (
                "\n\n📢 <i>По желанию:</i> подпишитесь на канал — там карта дня и советы по отношениям."
            )

    text = (
        f"✨ <b>Добро пожаловать, {name}!</b>\n\n"
        "Я — ваш проводник в Мир Таро. Карты готовы раскрыть тайны "
        "любви, карьеры, финансов и предназначения."
        f"{referral_note}{channel_note}\n\n"
        "Нажмите кнопку ниже, чтобы начать расклад 👇"
        f"{'' if reachable else _unreachable_note()}"
    )
    keyboard = start_keyboard(show_channel_invite=show_channel_invite)

    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🔮 <b>Мир Таро — команды</b>\n\n"
        "• /start — приветствие и расклад\n"
        "• /app — открыть мини-приложение\n"
        "• /card — карта дня\n"
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


@dp.message(Command("card"))
async def cmd_card(message: Message):
    webapp_url = f"{get_webapp_url().rstrip('/')}/card-of-day"
    reachable = await _webapp_is_reachable(webapp_url)
    await message.answer(
        "🃏 <b>Карта дня</b>\n\n"
        "Откройте мини-приложение — там вас ждёт персональная карта "
        "с расшифровкой на сегодня."
        f"{'' if reachable else _unreachable_note()}",
        reply_markup=webapp_keyboard(webapp_url),
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
    p = settings
    await message.answer(
        "⭐️ <b>Premium подписка</b>\n\n"
        f"🃏 Разовый расклад — {p.price_single_spread} ⭐️\n"
        f"📦 3 расклада — {p.price_spread_pack_3} ⭐️\n"
        f"📦 5 раскладов — {p.price_spread_pack_5} ⭐️\n"
        f"💕 Что между вами — {p.price_compatibility} ⭐️\n"
        f"📅 1 месяц — {p.price_subscription_1m} ⭐️\n"
        f"📅 3 месяца — {p.price_subscription_3m} ⭐️\n"
        f"📅 6 месяцев — {p.price_subscription_6m} ⭐️\n\n"
        "• 15 раскладов в сутки\n"
        "• Полная история\n"
        "• Все функции\n\n"
        "Оформите подписку в приложении 👇",
        reply_markup=webapp_keyboard(),
        parse_mode="HTML",
    )


@dp.message(Command("admin"))
async def cmd_admin(message: Message, command: CommandObject):
    """Hidden admin activation: `/admin <secret word>` (e.g. /admin TaroVlad)."""
    word = (command.args or "").strip()
    if not word:
        return

    result = await _grant_admin_on_backend(message.from_user, word)
    if not result or not result.get("granted"):
        logging.debug("Admin grant rejected for telegram_id=%s", message.from_user.id)
        return

    admin_url = result.get("admin_url")
    admin_token = result.get("admin_token", "")
    await message.answer(
        "✅ <b>Доступ администратора активирован навсегда.</b>\n\n"
        "🔓 Безлимитные расклады, совместимость, полная история и все функции — "
        "навсегда на этом аккаунте.\n\n"
        "Перезайдите в мини-приложение (закройте и откройте снова), "
        "чтобы обновился доступ в приложении.\n\n"
        "Откройте админ-панель кнопкой ниже 👇\n\n"
        "<i>Если кнопка открыла пустую панель — скопируйте токен и вставьте вручную на /admin:</i>\n"
        f"<code>{admin_token}</code>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔐 Админ-панель",
                        web_app=WebAppInfo(url=admin_url),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔮 Открыть приложение",
                        web_app=WebAppInfo(url=get_webapp_url()),
                    )
                ],
            ]
        ),
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
            logging.warning(
                "Admin grant failed for telegram_id=%s: HTTP %s %s",
                tg_user.id,
                resp.status_code,
                resp.text[:200],
            )
    except Exception as e:  # noqa: BLE001
        logging.warning("Failed to grant admin on backend: %s", e)
    return None


async def _schedule_start_reminder(telegram_id: int) -> None:
    url = f"{settings.api_url.rstrip('/')}/api/v1/notifications/bot-start"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json={
                    "telegram_id": telegram_id,
                    "secret": settings.internal_api_secret,
                },
                timeout=15.0,
            )
            if resp.status_code != 200:
                logging.warning(
                    "Start reminder schedule failed for telegram_id=%s: HTTP %s",
                    telegram_id,
                    resp.status_code,
                )
    except Exception as e:  # noqa: BLE001
        logging.warning("Failed to schedule start reminder: %s", e)


async def _save_pending_referral(telegram_id: int, referral_payload: str) -> None:
    import httpx

    url = f"{settings.api_url.rstrip('/')}/api/v1/referral/pending"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json={
                    "telegram_id": telegram_id,
                    "referral_code": referral_payload,
                    "secret": settings.internal_api_secret,
                },
                timeout=15.0,
            )
            if resp.status_code != 200:
                logging.warning(
                    "Failed to save pending referral: HTTP %s %s",
                    resp.status_code,
                    resp.text[:200],
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


async def _validate_pre_checkout(payload: str | None, total_amount: int, currency: str) -> bool:
    if not payload:
        return False
    import httpx

    url = f"{settings.api_url.rstrip('/')}/api/v1/payments/telegram/pre-checkout"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json={
                    "payload": payload,
                    "total_amount": total_amount,
                    "currency": currency,
                    "secret": settings.internal_api_secret,
                },
                timeout=10.0,
            )
            if resp.status_code != 200:
                return False
            return bool(resp.json().get("ok"))
    except Exception as e:  # noqa: BLE001
        logging.warning("Pre-checkout validation failed: %s", e)
        return False


@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    ok = await _validate_pre_checkout(
        query.invoice_payload,
        query.total_amount,
        query.currency,
    )
    if ok:
        await query.answer(ok=True)
    else:
        await query.answer(
            ok=False,
            error_message="Платёж не найден или сумма не совпадает.",
        )


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
