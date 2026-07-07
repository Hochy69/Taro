"""Schedule and trigger marketing push notifications."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.services import push_messages as copy
from app.core.config import settings
from app.infrastructure.database.models import (
    Notification,
    NotificationType,
    Payment,
    PaymentStatus,
    PaymentType,
    Spread,
    User,
)
from app.infrastructure.telegram_notify import send_telegram_message


async def notification_ever_sent(
    session: AsyncSession,
    user_id: int,
    ntype: NotificationType,
) -> bool:
    result = await session.execute(
        select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.notification_type == ntype,
            Notification.is_sent == True,
        )
    )
    return result.scalar_one_or_none() is not None


async def notification_sent_since(
    session: AsyncSession,
    user_id: int,
    ntype: NotificationType,
    since: datetime,
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


async def log_notification(
    session: AsyncSession,
    user: User,
    ntype: NotificationType,
    message: str,
    sent: bool,
) -> None:
    now = datetime.now(timezone.utc)
    session.add(
        Notification(
            user_id=user.id,
            notification_type=ntype,
            message=message,
            is_sent=sent,
            sent_at=now if sent else None,
        )
    )


async def send_user_push(
    session: AsyncSession,
    user: User,
    ntype: NotificationType,
    message: str,
    *,
    reply_markup: dict | None = None,
    parse_mode: str | None = "HTML",
) -> bool:
    sent = await send_telegram_message(
        user.telegram_id,
        message,
        parse_mode=parse_mode,
        reply_markup=reply_markup,
    )
    await log_notification(session, user, ntype, message, sent)
    return sent


def schedule_start_reminder(telegram_id: int) -> None:
    from app.infrastructure.tasks import send_start_no_webapp_reminder

    started_at = datetime.now(timezone.utc).isoformat()
    send_start_no_webapp_reminder.apply_async(
        args=[telegram_id, started_at],
        countdown=30 * 60,
        task_id=f"start_no_webapp_{telegram_id}",
    )


def schedule_compat_abandon_reminder(user_id: int) -> None:
    from app.infrastructure.tasks import send_compat_abandon_reminder

    viewed_at = datetime.now(timezone.utc).isoformat()
    send_compat_abandon_reminder.apply_async(
        args=[user_id, viewed_at],
        countdown=2 * 60 * 60,
        task_id=f"compat_abandon_{user_id}",
    )


def schedule_limit_followup(user_id: int, days_until_free: int) -> None:
    from app.infrastructure.tasks import send_free_limit_followup

    send_free_limit_followup.apply_async(
        args=[user_id, days_until_free],
        countdown=24 * 60 * 60,
        task_id=f"free_limit_followup_{user_id}",
    )


def schedule_compat_upsell(user_id: int) -> None:
    from app.infrastructure.tasks import send_compat_paid_upsell

    send_compat_paid_upsell.apply_async(
        args=[user_id],
        countdown=5 * 60,
        task_id=f"compat_upsell_{user_id}",
    )


def schedule_spread_milestone_push(spread_id: int) -> None:
    from app.infrastructure.tasks import send_spread_milestone_push

    send_spread_milestone_push.apply_async(
        args=[spread_id],
        countdown=2,
        task_id=f"spread_milestone_{spread_id}",
    )


def schedule_free_limit_hit_push(user_id: int) -> None:
    from app.infrastructure.tasks import send_free_limit_hit_push

    send_free_limit_hit_push.apply_async(
        args=[user_id],
        countdown=2,
        task_id=f"free_limit_hit_{user_id}",
    )


async def on_spread_interpreted(session: AsyncSession, spread_id: int) -> None:
    from app.application.services.spread_service import SpreadService

    result = await session.execute(
        select(Spread).where(Spread.id == spread_id)
    )
    spread = result.scalar_one_or_none()
    if not spread or spread.quota_from_bonus:
        return

    user_result = await session.execute(
        select(User).options(selectinload(User.limits)).where(User.id == spread.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user or user.is_blocked or user.is_admin:
        return

    spread_service = SpreadService(session)
    if await spread_service.is_premium(user.id):
        return

    if not user.limits:
        return

    used = user.limits.daily_spreads_used
    if used == 1:
        ntype = NotificationType.SPREAD_FIRST
        msg = copy.after_first_spread_message()
        keyboard = copy.compat_keyboard()
    elif used == 2:
        ntype = NotificationType.SPREAD_SECOND
        msg = copy.after_second_spread_message()
        keyboard = copy.spread_keyboard()
    elif used == 3:
        ntype = NotificationType.SPREAD_THIRD
        msg = copy.after_third_spread_message()
        keyboard = copy.app_keyboard()
        elapsed = (date.today() - user.limits.last_reset_date).days
        days_left = max(1, settings.free_spread_period_days - elapsed)
        schedule_limit_followup(user.id, days_left)
    else:
        return

    if await notification_ever_sent(session, user.id, ntype):
        return

    await send_user_push(session, user, ntype, msg, reply_markup=keyboard)


async def on_free_limit_blocked(session: AsyncSession, user: User) -> None:
    if user.is_admin:
        return

    from app.application.services.spread_service import SpreadService

    if await SpreadService(session).is_premium(user.id):
        return

    ntype = NotificationType.FREE_LIMIT_HIT
    if await notification_sent_since(
        session,
        user.id,
        ntype,
        datetime.now(timezone.utc) - timedelta(days=settings.free_spread_period_days),
    ):
        return

    msg = copy.free_limit_exhausted_message()
    await send_user_push(session, user, ntype, msg, reply_markup=copy.app_keyboard())


async def on_compatibility_paid(session: AsyncSession, payment: Payment) -> None:
    if payment.payment_type != PaymentType.COMPATIBILITY:
        return
    if payment.status != PaymentStatus.COMPLETED:
        return

    user_result = await session.execute(select(User).where(User.id == payment.user_id))
    user = user_result.scalar_one_or_none()
    if not user or user.is_blocked:
        return

    if await notification_ever_sent(session, user.id, NotificationType.COMPAT_PAID_UPSELL):
        return

    schedule_compat_upsell(user.id)
