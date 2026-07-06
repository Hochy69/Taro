import asyncio
import logging
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.infrastructure.celery_app import celery_app
from app.infrastructure.database.models import (
    Notification,
    NotificationType,
    Subscription,
    SubscriptionStatus,
    User,
)
from app.infrastructure.database.session import async_session
from app.infrastructure.telegram_notify import (
    escape_telegram_html,
    send_telegram_message,
    web_app_button,
    web_app_keyboard,
)

logger = logging.getLogger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def utc_day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


async def _notification_already_sent(
    session,
    user_id: int,
    ntype: NotificationType,
    day: date,
) -> bool:
    day_start, day_end = utc_day_bounds(day)
    result = await session.execute(
        select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.notification_type == ntype,
            Notification.created_at >= day_start,
            Notification.created_at < day_end,
            Notification.is_sent == True,
        )
    )
    return result.scalar_one_or_none() is not None


@celery_app.task(name="app.infrastructure.tasks.check_subscription_notifications")
def check_subscription_notifications():
    run_async(_check_subscription_notifications())


async def _check_subscription_notifications():
    now = datetime.now(timezone.utc)
    today = now.date()

    async with async_session() as session:
        result = await session.execute(
            select(Subscription)
            .options(selectinload(Subscription.user))
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
        )
        subscriptions = result.scalars().all()

        for sub in subscriptions:
            user = sub.user
            if not user or user.is_blocked:
                continue

            expires = sub.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            days_left = (expires.date() - today).days

            if days_left == 3:
                msg = (
                    f"✨ {user.first_name or 'Дорогой друг'}, ваша Premium-подписка "
                    f"заканчивается через 3 дня. Продлите, чтобы не потерять доступ "
                    f"к полной истории раскладов!"
                )
                ntype = NotificationType.SUBSCRIPTION_EXPIRING_3D
            elif days_left == 0:
                msg = (
                    f"🌙 {user.first_name or 'Дорогой друг'}, сегодня последний день "
                    f"вашей подписки. Карты ждут вас — продлите Premium!"
                )
                ntype = NotificationType.SUBSCRIPTION_EXPIRING_TODAY
            elif days_left < 0:
                msg = (
                    f"💫 {user.first_name or 'Дорогой друг'}, ваша подписка завершилась. "
                    f"Вернитесь — карты приготовили для вас новое послание!"
                )
                ntype = NotificationType.SUBSCRIPTION_EXPIRED
                sub.status = SubscriptionStatus.EXPIRED
                if not user.is_admin:
                    user.is_premium = False
            else:
                continue

            if await _notification_already_sent(session, user.id, ntype, today):
                continue

            sent = await send_telegram_message(user.telegram_id, msg, parse_mode=None)
            session.add(
                Notification(
                    user_id=user.id,
                    notification_type=ntype,
                    message=msg,
                    is_sent=sent,
                    sent_at=now if sent else None,
                )
            )

        await session.commit()


@celery_app.task(name="app.infrastructure.tasks.send_daily_card_push")
def send_daily_card_push():
    run_async(_send_daily_card_push())


async def _send_daily_card_push():
    from app.application.services.card_of_day_service import get_card_of_day
    from app.core.config import settings

    now = datetime.now(timezone.utc)
    today = now.date()
    webapp = settings.telegram_webapp_url.rstrip("/")
    card_url = f"{webapp}/card-of-day"

    sent_count = 0
    skipped = 0
    failed = 0

    async with async_session() as session:
        result = await session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(
                User.is_blocked == False,
                User.daily_card_push == True,
            )
        )
        users = result.scalars().all()
        logger.info("Daily card push: %s eligible users", len(users))

        for user in users:
            if await _notification_already_sent(session, user.id, NotificationType.CARD_OF_DAY, today):
                skipped += 1
                continue

            name = user.profile.name if user.profile and user.profile.name else (user.first_name or "друг")
            zodiac = user.profile.zodiac_sign if user.profile else None
            try:
                data = await get_card_of_day(session, user.id, name, zodiac, today)
            except Exception:
                logger.exception("Daily card generation failed for user_id=%s", user.id)
                failed += 1
                continue

            rev = " (перевёрнутая)" if data["card"]["is_reversed"] else ""
            spread_url = f"{webapp}/"
            card_name = escape_telegram_html(data["card"]["name"])
            meaning = escape_telegram_html(data["meaning"])
            msg = (
                f"🃏 <b>Карта дня — {card_name}</b>{rev}\n\n"
                f"{meaning}\n\n"
                f"💫 Карты намекают — хотите уточнить расклад?\n\n"
                f"Нажмите кнопку ниже, чтобы открыть карту в приложении."
            )
            keyboard = web_app_keyboard(
                web_app_button("🃏 Открыть карту", card_url),
                web_app_button("🔮 Расклад", spread_url),
            )
            sent = await send_telegram_message(user.telegram_id, msg, reply_markup=keyboard)
            session.add(
                Notification(
                    user_id=user.id,
                    notification_type=NotificationType.CARD_OF_DAY,
                    message=msg,
                    is_sent=sent,
                    sent_at=now if sent else None,
                )
            )
            if sent:
                sent_count += 1
            else:
                failed += 1

        await session.commit()

    logger.info(
        "Daily card push finished: sent=%s skipped=%s failed=%s",
        sent_count,
        skipped,
        failed,
    )


@celery_app.task(name="app.infrastructure.tasks.check_inactive_users")
def check_inactive_users():
    run_async(_check_inactive_users())


async def _check_inactive_users():
    now = datetime.now(timezone.utc)
    today = now.date()

    async with async_session() as session:
        result = await session.execute(
            select(User).options(selectinload(User.profile)).where(User.is_blocked == False)
        )
        users = result.scalars().all()

        for user in users:
            if not user.last_active_at:
                continue

            days_inactive = (now - user.last_active_at).days
            name = user.profile.name if user.profile and user.profile.name else user.first_name or "Дорогой друг"

            if days_inactive == 3:
                msg = f"🃏 {name}, карты соскучились по вам! Загляните — возможно, судьба приготовила знак."
                ntype = NotificationType.INACTIVE_3D
            elif days_inactive == 7:
                msg = f"✨ {name}, прошла неделя с вашего последнего визита. Новый расклад может прояснить ситуацию."
                ntype = NotificationType.INACTIVE_7D
            elif days_inactive == 14:
                msg = f"🌟 {name}, две недели без раскладов — вселенная наверняка приготовила вам послание!"
                ntype = NotificationType.INACTIVE_14D
            else:
                continue

            if await _notification_already_sent(session, user.id, ntype, today):
                continue

            sent = await send_telegram_message(user.telegram_id, msg, parse_mode=None)
            session.add(
                Notification(
                    user_id=user.id,
                    notification_type=ntype,
                    message=msg,
                    is_sent=sent,
                    sent_at=now if sent else None,
                )
            )

        await session.commit()
