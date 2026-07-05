from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.schemas import AdminGrantRequest
from app.application.services.admin_stats_service import AdminStatsService
from app.core.config import settings
from app.core.security import create_admin_token, decode_token
from app.infrastructure.database.models import (
    Payment,
    PaymentStatus,
    Profile,
    User,
    UserLimit,
)
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/grant")
async def grant_admin(body: AdminGrantRequest, db: AsyncSession = Depends(get_db)):
    """Hidden bootstrap endpoint used by the bot's `/admin <word>` command.

    Requires both the internal service secret and the admin secret word.
    Grants the caller permanent full access (admin + premium) and returns a
    token for the admin dashboard.
    """
    if body.internal_secret != settings.internal_api_secret:
        raise HTTPException(status_code=403, detail="forbidden")
    if body.word.strip().lower() != settings.admin_secret_word.strip().lower():
        raise HTTPException(status_code=403, detail="forbidden")

    result = await db.execute(select(User).where(User.telegram_id == body.telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            telegram_id=body.telegram_id,
            username=body.username,
            first_name=body.first_name,
        )
        db.add(user)
        await db.flush()
        db.add(Profile(user_id=user.id, name=body.first_name))
        await db.flush()

    user.is_admin = True
    user.is_premium = True
    if user.terms_accepted_at is None:
        user.terms_accepted_at = datetime.now(timezone.utc)

    limit_result = await db.execute(select(UserLimit).where(UserLimit.user_id == user.id))
    limits = limit_result.scalar_one_or_none()
    if not limits:
        limits = UserLimit(user_id=user.id)
        db.add(limits)
    limits.bonus_spreads = 999999
    limits.compatibility_credits = 999999
    limits.daily_spreads_used = 0

    await db.flush()

    token = create_admin_token(user.id)
    return {
        "granted": True,
        "admin_token": token,
        "admin_url": f"{settings.frontend_url.rstrip('/')}/admin?token={token}",
        "message": "Полный доступ навсегда: безлимитные расклады, совместимость, история, все функции.",
    }


async def get_admin(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token, settings.admin_jwt_secret or settings.jwt_secret_key)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    user_id = int(payload["sub"])
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_admin.is_(True), User.is_blocked.is_(False))
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload


@router.get("/dashboard")
async def dashboard(admin=Depends(get_admin), db: AsyncSession = Depends(get_db)):
    return await AdminStatsService(db).get_dashboard()


@router.get("/users")
async def list_users(
    admin=Depends(get_admin),
    db: AsyncSession = Depends(get_db),
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    query = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    if search:
        query = query.where(
            User.username.ilike(f"%{search}%") | User.first_name.ilike(f"%{search}%")
        )
    result = await db.execute(query)
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "telegram_id": u.telegram_id,
            "username": u.username,
            "first_name": u.first_name,
            "is_premium": u.is_premium,
            "is_blocked": u.is_blocked,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.post("/users/{user_id}/block")
async def block_user(user_id: int, admin=Depends(get_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404)
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot block admin")
    user.is_blocked = True
    return {"status": "blocked"}


@router.post("/users/{user_id}/unblock")
async def unblock_user(user_id: int, admin=Depends(get_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404)
    user.is_blocked = False
    return {"status": "unblocked"}


@router.get("/finance")
async def finance_stats(admin=Depends(get_admin), db: AsyncSession = Depends(get_db)):
    from app.application.services.admin_stats_service import TEST_TELEGRAM_IDS

    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    async def revenue_since(since: datetime) -> int:
        return int(
            (
                await db.execute(
                    select(func.coalesce(func.sum(Payment.stars_amount), 0))
                    .join(User, Payment.user_id == User.id)
                    .where(
                        User.telegram_id.notin_(TEST_TELEGRAM_IDS),
                        Payment.status == PaymentStatus.COMPLETED,
                        Payment.created_at >= since,
                    )
                )
            ).scalar()
            or 0
        )

    return {
        "revenue_day": await revenue_since(day_ago),
        "revenue_week": await revenue_since(week_ago),
        "revenue_month": await revenue_since(month_ago),
        "currency": "Telegram Stars",
    }
