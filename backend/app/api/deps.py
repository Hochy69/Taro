from datetime import date
from typing import Annotated

from fastapi import Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import create_access_token, decode_token, verify_telegram_webapp_data
from app.core.config import settings
from app.infrastructure.database.models import Profile, User
from app.infrastructure.database.session import get_db

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = int(payload["sub"])
    result = await db.execute(
        select(User)
        .options(selectinload(User.profile), selectinload(User.limits))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user or user.is_blocked:
        raise HTTPException(status_code=401, detail="User not found or blocked")

    # Keep DAU/MAU accurate: touch activity on every authenticated request.
    from datetime import datetime, timezone

    user.last_active_at = datetime.now(timezone.utc)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_terms_accepted(user: CurrentUser) -> User:
    """Gate that blocks access until the user has accepted the offer/terms."""
    if user.terms_accepted_at is None:
        raise HTTPException(
            status_code=451,
            detail="Необходимо принять пользовательское соглашение (оферту).",
        )
    return user


RequireTermsUser = Annotated[User, Depends(require_terms_accepted)]


async def _load_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> User | None:
    result = await db.execute(
        select(User)
        .options(selectinload(User.profile), selectinload(User.limits))
        .where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def authenticate_telegram_user(db: AsyncSession, init_data: str) -> tuple[User, str]:
    from sqlalchemy.exc import IntegrityError

    from app.application.services.referral_service import ReferralService

    parsed = verify_telegram_webapp_data(init_data, settings.telegram_bot_token)
    if not parsed or "user" not in parsed:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")

    tg_user = parsed["user"]
    telegram_id = tg_user["id"]

    user = await _load_user_by_telegram_id(db, telegram_id)
    is_new = False

    if not user:
        is_new = True
        try:
            user = User(
                telegram_id=telegram_id,
                username=tg_user.get("username"),
                first_name=tg_user.get("first_name"),
                last_name=tg_user.get("last_name"),
                language_code=tg_user.get("language_code", "ru"),
            )
            db.add(user)
            await db.flush()
            db.add(Profile(user_id=user.id))
            await db.flush()
        except IntegrityError:
            await db.rollback()
            is_new = False
        # Re-load with relationships eagerly populated so that building the
        # response never triggers an (async-unsafe) lazy load.
        user = await _load_user_by_telegram_id(db, telegram_id)
        if not user:
            raise HTTPException(status_code=500, detail="User bootstrap failed")

        if is_new:
            referral_service = ReferralService(db)
            await referral_service.ensure_referral_code(user)
            await referral_service.process_signup(user, parsed.get("start_param"))
    else:
        from datetime import datetime, timezone

        user.last_active_at = datetime.now(timezone.utc)

    token = create_access_token({"sub": str(user.id)})
    return user, token
