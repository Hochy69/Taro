import asyncio
import logging
from collections.abc import Callable
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from celery.signals import worker_process_init, worker_process_shutdown
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.infrastructure.celery_app import celery_app
from app.infrastructure.database.models import (
    Notification,
    NotificationType,
    Payment,
    PaymentStatus,
    PaymentType,
    Subscription,
    SubscriptionStatus,
    User,
)
from app.infrastructure.database.session import async_session, engine
from app.infrastructure.telegram_notify import (
    escape_telegram_html,
    send_telegram_message,
    web_app_button,
    web_app_keyboard,
)

logger = logging.getLogger(__name__)

MSK = ZoneInfo("Europe/Moscow")


@worker_process_init.connect
def _init_celery_worker_process(**_kwargs) -> None:
    """One event loop per Celery child process (prefork pool)."""
    asyncio.set_event_loop(asyncio.new_event_loop())


@worker_process_shutdown.connect
def _shutdown_celery_worker_process(**_kwargs) -> None:
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        return
    try:
        loop.run_until_complete(engine.dispose())
    except Exception:
        logger.exception("Failed to dispose SQLAlchemy engine on worker shutdown")
    finally:
        loop.close()
        asyncio.set_event_loop(None)


def run_async(coro):
    """Run async Celery task code on the worker's persistent event loop."""
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def utc_day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


def msk_day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=MSK)
    end = start + timedelta(days=1)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def msk_today() -> date:
    return datetime.now(MSK).date()


async def _notification_already_sent(
    session,
    user_id: int,
    ntype: NotificationType,
    day: date,
    *,
    day_bounds: Callable[[date], tuple[datetime, datetime]] | None = None,
) -> bool:
    day_start, day_end = (day_bounds or utc_day_bounds)(day)
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
    today = msk_today()
    webapp = settings.telegram_webapp_url.rstrip("/")
    card_url = f"{webapp}/card-of-day"
    compat_url = f"{webapp}/compatibility"

    sent_count = 0
    skipped = 0
    failed = 0

    logger.info("Daily card push starting for MSK date=%s", today)

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
            try:
                if await _notification_already_sent(
                    session,
                    user.id,
                    NotificationType.CARD_OF_DAY,
                    today,
                    day_bounds=msk_day_bounds,
                ):
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
                card_name = escape_telegram_html(data["card"]["name"])
                meaning = escape_telegram_html(data["meaning"])
                intro = (
                    "🃏 <b>Ваша карта дня готова</b>\n\n"
                    f"<b>{card_name}</b>{rev}\n{meaning}\n\n"
                    "Откройте приложение — послание дня + совет карт.\n"
                    "А если день про отношения — загляните в «Что между вами» 💕"
                )
                keyboard = web_app_keyboard(
                    web_app_button("🃏 Открыть карту", card_url),
                    web_app_button("💕 Что между вами", compat_url),
                )
                sent = await send_telegram_message(user.telegram_id, intro, reply_markup=keyboard)
                session.add(
                    Notification(
                        user_id=user.id,
                        notification_type=NotificationType.CARD_OF_DAY,
                        message=intro,
                        is_sent=sent,
                        sent_at=now if sent else None,
                    )
                )
                if sent:
                    sent_count += 1
                else:
                    failed += 1
            except Exception:
                logger.exception("Daily card push failed for user_id=%s", user.id)
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


async def _notification_ever_sent(session, user_id: int, ntype: NotificationType) -> bool:
    result = await session.execute(
        select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.notification_type == ntype,
            Notification.is_sent == True,
        )
    )
    return result.scalar_one_or_none() is not None


async def _notification_sent_since(
    session, user_id: int, ntype: NotificationType, since: datetime
) -> bool:
    result = await session.execute(
        select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.notification_type == ntype,
            Notification.is_sent == True,
            Notification.created_at >= since,
        )
    )
    return result.scalar_one_or_none() is not None


@celery_app.task(name="app.infrastructure.tasks.send_start_no_webapp_reminder")
def send_start_no_webapp_reminder(telegram_id: int, started_at_iso: str):
    run_async(_send_start_no_webapp_reminder(telegram_id, started_at_iso))


async def _send_start_no_webapp_reminder(telegram_id: int, started_at_iso: str):
    from app.application.services import push_messages as copy

    started_at = datetime.fromisoformat(started_at_iso)
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()

        if user:
            if await _notification_sent_since(
                session,
                user.id,
                NotificationType.START_NO_WEBAPP,
                now - timedelta(days=7),
            ):
                return
            if user.last_active_at and user.last_active_at > started_at + timedelta(minutes=2):
                return

        msg = copy.start_no_webapp_message()
        keyboard = copy.start_no_webapp_keyboard()
        sent = await send_telegram_message(telegram_id, msg, reply_markup=keyboard)

        if user and sent:
            session.add(
                Notification(
                    user_id=user.id,
                    notification_type=NotificationType.START_NO_WEBAPP,
                    message=msg,
                    is_sent=True,
                    sent_at=now,
                )
            )
            await session.commit()


@celery_app.task(name="app.infrastructure.tasks.send_compat_abandon_reminder")
def send_compat_abandon_reminder(user_id: int, viewed_at_iso: str):
    run_async(_send_compat_abandon_reminder(user_id, viewed_at_iso))


async def _send_compat_abandon_reminder(user_id: int, viewed_at_iso: str):
    from app.application.services import push_messages as copy

    viewed_at = datetime.fromisoformat(viewed_at_iso)
    if viewed_at.tzinfo is None:
        viewed_at = viewed_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    async with async_session() as session:
        result = await session.execute(
            select(User).options(selectinload(User.limits)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user or user.is_blocked or user.is_admin or user.is_premium:
            return

        limits = user.limits
        if limits and limits.compatibility_credits > 0:
            return

        paid_since = await session.execute(
            select(Payment.id).where(
                Payment.user_id == user_id,
                Payment.payment_type == PaymentType.COMPATIBILITY,
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= viewed_at,
            )
        )
        if paid_since.scalar_one_or_none() is not None:
            return

        if await _notification_sent_since(
            session, user.id, NotificationType.COMPAT_VIEW_ABANDONED, now - timedelta(days=1)
        ):
            return

        msg = copy.compat_abandon_message()
        keyboard = copy.compat_keyboard()
        sent = await send_telegram_message(user.telegram_id, msg, reply_markup=keyboard)
        session.add(
            Notification(
                user_id=user.id,
                notification_type=NotificationType.COMPAT_VIEW_ABANDONED,
                message=msg,
                is_sent=sent,
                sent_at=now if sent else None,
            )
        )
        await session.commit()


@celery_app.task(name="app.infrastructure.tasks.send_free_limit_followup")
def send_free_limit_followup(user_id: int, days_until_free: int):
    run_async(_send_free_limit_followup(user_id, days_until_free))


async def _send_free_limit_followup(user_id: int, days_until_free: int):
    from app.application.services import push_messages as copy
    from app.application.services.spread_service import SpreadService

    now = datetime.now(timezone.utc)
    async with async_session() as session:
        result = await session.execute(
            select(User).options(selectinload(User.limits)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user or user.is_blocked or user.is_admin:
            return
        if await SpreadService(session).is_premium(user.id):
            return

        if await _notification_ever_sent(session, user.id, NotificationType.FREE_LIMIT_FOLLOWUP):
            return

        msg = copy.limit_followup_message(days_until_free)
        keyboard = copy.app_keyboard()
        sent = await send_telegram_message(user.telegram_id, msg, reply_markup=keyboard)
        session.add(
            Notification(
                user_id=user.id,
                notification_type=NotificationType.FREE_LIMIT_FOLLOWUP,
                message=msg,
                is_sent=sent,
                sent_at=now if sent else None,
            )
        )
        await session.commit()


@celery_app.task(name="app.infrastructure.tasks.send_compat_paid_upsell")
def send_compat_paid_upsell(user_id: int):
    run_async(_send_compat_paid_upsell(user_id))


async def _send_compat_paid_upsell(user_id: int):
    from app.application.services import push_messages as copy

    now = datetime.now(timezone.utc)
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or user.is_blocked:
            return

        bundle = await session.execute(
            select(Payment.id).where(
                Payment.user_id == user_id,
                Payment.payment_type == PaymentType.LOVE_BUNDLE,
                Payment.status == PaymentStatus.COMPLETED,
            )
        )
        if bundle.scalar_one_or_none() is not None:
            return

        if await _notification_ever_sent(session, user.id, NotificationType.COMPAT_PAID_UPSELL):
            return

        msg = copy.compat_paid_upsell_message()
        keyboard = copy.premium_keyboard()
        sent = await send_telegram_message(user.telegram_id, msg, reply_markup=keyboard)
        session.add(
            Notification(
                user_id=user.id,
                notification_type=NotificationType.COMPAT_PAID_UPSELL,
                message=msg,
                is_sent=sent,
                sent_at=now if sent else None,
            )
        )
        await session.commit()


@celery_app.task(name="app.infrastructure.tasks.send_free_limit_hit_push")
def send_free_limit_hit_push(user_id: int):
    run_async(_send_free_limit_hit_push(user_id))


async def _send_free_limit_hit_push(user_id: int):
    from app.application.services.marketing_push_service import on_free_limit_blocked

    async with async_session() as session:
        from sqlalchemy import select
        from app.infrastructure.database.models import User

        user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            return
        try:
            await on_free_limit_blocked(session, user)
            await session.commit()
        except Exception:
            logger.exception("Free limit hit push failed for user_id=%s", user_id)


@celery_app.task(name="app.infrastructure.tasks.send_spread_milestone_push")
def send_spread_milestone_push(spread_id: int):
    run_async(_send_spread_milestone_push(spread_id))


async def _send_spread_milestone_push(spread_id: int):
    from app.application.services.marketing_push_service import on_spread_interpreted

    async with async_session() as session:
        try:
            await on_spread_interpreted(session, spread_id)
            await session.commit()
        except Exception:
            logger.exception("Spread milestone push failed for spread_id=%s", spread_id)


@celery_app.task(name="app.infrastructure.tasks.send_weekly_referral_push")
def send_weekly_referral_push():
    run_async(_send_weekly_referral_push())


async def _send_weekly_referral_push():
    from app.application.services import push_messages as copy

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.is_blocked == False,
                User.last_active_at.isnot(None),
                User.last_active_at >= week_ago,
            )
        )
        users = result.scalars().all()

        for user in users:
            if await _notification_sent_since(
                session, user.id, NotificationType.WEEKLY_REFERRAL, week_ago
            ):
                continue

            msg = copy.weekly_referral_message()
            keyboard = copy.app_keyboard()
            sent = await send_telegram_message(user.telegram_id, msg, reply_markup=keyboard)
            session.add(
                Notification(
                    user_id=user.id,
                    notification_type=NotificationType.WEEKLY_REFERRAL,
                    message=msg,
                    is_sent=sent,
                    sent_at=now if sent else None,
                )
            )

        await session.commit()
