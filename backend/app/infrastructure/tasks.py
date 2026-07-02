import asyncio
from datetime import datetime, timedelta, timezone

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


async def _send_telegram_message(telegram_id: int, text: str) -> bool:
    from app.core.config import settings
    import httpx

    if not settings.telegram_bot_token:
        return False
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json={"chat_id": telegram_id, "text": text, "parse_mode": "HTML"},
        )
        return response.status_code == 200


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.infrastructure.tasks.check_subscription_notifications")
def check_subscription_notifications():
    run_async(_check_subscription_notifications())


async def _check_subscription_notifications():
    now = datetime.now(timezone.utc)
    three_days = now + timedelta(days=3)

    async with async_session() as session:
        result = await session.execute(
            select(Subscription)
            .options(selectinload(Subscription.user))
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
        )
        subscriptions = result.scalars().all()

        for sub in subscriptions:
            user = sub.user
            if not user:
                continue

            expires = sub.expires_at
            days_left = (expires - now).days

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
                user.is_premium = False
            else:
                continue

            sent = await _send_telegram_message(user.telegram_id, msg)
            notification = Notification(
                user_id=user.id,
                notification_type=ntype,
                message=msg,
                is_sent=sent,
                sent_at=now if sent else None,
            )
            session.add(notification)

        await session.commit()


@celery_app.task(name="app.infrastructure.tasks.check_inactive_users")
def check_inactive_users():
    run_async(_check_inactive_users())


async def _check_inactive_users():
    now = datetime.now(timezone.utc)

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

            sent = await _send_telegram_message(user.telegram_id, msg)
            notification = Notification(
                user_id=user.id,
                notification_type=ntype,
                message=msg,
                is_sent=sent,
                sent_at=now if sent else None,
            )
            session.add(notification)

        await session.commit()
