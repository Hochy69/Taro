from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession, RequireTermsUser, authenticate_telegram_user
from app.application.dto.schemas import (
    AcceptTermsResponse,
    AIResultResponse,
    CardResponse,
    CategoryResponse,
    CreateSpreadRequest,
    FavoriteRequest,
    HistoryItemResponse,
    LimitsResponse,
    PaymentCreateRequest,
    PaymentResponse,
    PricingResponse,
    ProfileUpdate,
    ReferralPendingRequest,
    ReferralResponse,
    ShareMessageResponse,
    SpreadDetailResponse,
    SpreadResponse,
    StarsConfirmRequest,
    SubscriptionPlanResponse,
    TelegramAuthRequest,
    TelegramAuthResponse,
    UserResponse,
)
from app.application.services.payment_service import PLAN_DURATIONS, PaymentService
from app.application.services.referral_service import ReferralService
from app.application.services.share_service import prepare_spread_share_message
from app.application.services.spread_service import SpreadService
from app.application.services.tarot_ai_service import get_zodiac_sign
from app.core.config import settings
from app.core.security import create_access_token
from app.infrastructure.database.models import (
    Category,
    Favorite,
    PaymentType,
    Spread,
    SpreadCard,
    SpreadStatus,
    SubscriptionPlan,
)

router = APIRouter()


@router.post("/auth/telegram", response_model=TelegramAuthResponse)
async def auth_telegram(body: TelegramAuthRequest, db: DbSession):
    user, token = await authenticate_telegram_user(db, body.init_data)
    return _build_auth_response(user, token)


@router.post("/auth/dev", response_model=TelegramAuthResponse)
async def auth_dev(db: DbSession):
    """Auth for local dev and browser testing outside Telegram WebApp."""
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Not found")

    from sqlalchemy.exc import IntegrityError

    from app.infrastructure.database.models import Profile, User

    async def _load_dev_user() -> User | None:
        result = await db.execute(
            select(User)
            .options(selectinload(User.profile), selectinload(User.limits))
            .where(User.telegram_id == 0)
        )
        return result.scalar_one_or_none()

    user = await _load_dev_user()
    if not user:
        try:
            user = User(
                telegram_id=0,
                username="dev_user",
                first_name="Dev",
                language_code="ru",
            )
            db.add(user)
            await db.flush()
            db.add(Profile(user_id=user.id, name="Dev"))
            await db.flush()
        except IntegrityError:
            await db.rollback()
            user = await _load_dev_user()
            if not user:
                raise HTTPException(status_code=500, detail="Dev user bootstrap failed")
        else:
            result = await db.execute(
                select(User)
                .options(selectinload(User.profile), selectinload(User.limits))
                .where(User.id == user.id)
            )
            user = result.scalar_one()

    token = create_access_token({"sub": str(user.id)})
    return _build_auth_response(user, token)


def _build_auth_response(user, token: str) -> TelegramAuthResponse:
    is_returning = user.profile is not None and user.profile.name is not None
    last_category = user.profile.last_category_slug if user.profile else None

    profile_data = None
    if user.profile:
        profile_data = ProfileUpdate(
            name=user.profile.name,
            birth_date=user.profile.birth_date,
            zodiac_sign=user.profile.zodiac_sign,
        )

    return TelegramAuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            telegram_id=user.telegram_id,
            first_name=user.first_name,
            username=user.username,
            is_premium=user.is_premium,
            terms_accepted=user.terms_accepted_at is not None,
            profile=profile_data,
        ),
        is_returning=is_returning,
        last_category=last_category,
    )


@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories(db: DbSession):
    result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.sort_order)
    )
    return result.scalars().all()


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser):
    profile_data = None
    if user.profile:
        profile_data = ProfileUpdate(
            name=user.profile.name,
            birth_date=user.profile.birth_date,
            zodiac_sign=user.profile.zodiac_sign,
        )
    return UserResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        first_name=user.first_name,
        username=user.username,
        is_premium=user.is_premium,
        terms_accepted=user.terms_accepted_at is not None,
        profile=profile_data,
    )


@router.post("/me/accept-terms", response_model=AcceptTermsResponse)
async def accept_terms(user: CurrentUser, db: DbSession):
    """Record the user's one-time acceptance of the offer/terms agreement."""
    if user.terms_accepted_at is None:
        user.terms_accepted_at = datetime.now(timezone.utc)
        await db.flush()
    return AcceptTermsResponse(
        terms_accepted=True,
        accepted_at=user.terms_accepted_at,
    )


@router.get("/referral", response_model=ReferralResponse)
async def get_referral(user: RequireTermsUser, db: DbSession):
    """Personal referral link and invite stats."""
    info = await ReferralService(db).get_info(user)
    return ReferralResponse(**info)


@router.post("/referral/pending")
async def save_referral_pending(body: ReferralPendingRequest, db: DbSession):
    """Store a pending referral from the bot /start deep link (internal)."""
    if body.secret != settings.internal_api_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    await ReferralService(db).save_pending(body.telegram_id, body.referral_code)
    return {"ok": True}


@router.get("/limits", response_model=LimitsResponse)
async def get_limits(user: CurrentUser, db: DbSession):
    from datetime import datetime, time, timedelta

    service = SpreadService(db)
    can_spread, used, limit = await service.check_daily_limit(user)
    is_premium = await service._is_premium(user.id)
    bonus = user.limits.bonus_spreads if user.limits else 0
    period_days = 1 if is_premium else settings.free_spread_period_days

    next_available_at: str | None = None
    if not can_spread and user.limits is not None:
        next_date = user.limits.last_reset_date + timedelta(days=period_days)
        next_available_at = datetime.combine(next_date, time.min).isoformat()

    return LimitsResponse(
        can_spread=can_spread,
        used_today=used,
        daily_limit=limit,
        is_premium=is_premium,
        bonus_spreads=bonus,
        period_days=period_days,
        next_available_at=next_available_at,
    )


@router.get("/pricing", response_model=PricingResponse)
async def get_pricing():
    return PricingResponse(
        single_spread=settings.price_single_spread,
        plans=[
            SubscriptionPlanResponse(
                plan="month_1",
                stars=settings.price_subscription_1m,
                duration_days=30,
                daily_spreads=settings.premium_daily_spreads,
                features=["15 раскладов в сутки", "Вся история", "Все функции"],
            ),
            SubscriptionPlanResponse(
                plan="month_3",
                stars=settings.price_subscription_3m,
                duration_days=90,
                daily_spreads=settings.premium_daily_spreads,
                features=["15 раскладов в сутки", "Вся история", "Экономия 11%"],
            ),
            SubscriptionPlanResponse(
                plan="month_6",
                stars=settings.price_subscription_6m,
                duration_days=180,
                daily_spreads=settings.premium_daily_spreads,
                features=["15 раскладов в сутки", "Вся история", "Экономия 22%"],
            ),
        ],
    )


@router.post("/spreads", response_model=SpreadResponse)
async def create_spread(body: CreateSpreadRequest, user: RequireTermsUser, db: DbSession):
    service = SpreadService(db)
    try:
        profile_data = None
        if body.profile:
            profile_data = body.profile.model_dump()
            if profile_data.get("birth_date") and not profile_data.get("zodiac_sign"):
                profile_data["zodiac_sign"] = get_zodiac_sign(profile_data["birth_date"])

        spread = await service.create_spread(
            user=user,
            category_slug=body.category_slug,
            situation=body.situation,
            emotion=body.emotion,
            profile_data=profile_data,
        )
        result = await db.execute(
            select(Spread)
            .options(
                selectinload(Spread.cards).selectinload(SpreadCard.card),
                selectinload(Spread.category),
            )
            .where(Spread.id == spread.id)
        )
        spread = result.scalar_one()

        return _spread_to_response(spread)
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Бесплатный расклад доступен раз в {settings.free_spread_period_days} дня. "
                "Оформите подписку или купите разовый расклад за звёзды, чтобы продолжить."
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/spreads/{spread_id}/interpret", response_model=AIResultResponse)
async def interpret_spread(spread_id: int, user: RequireTermsUser, db: DbSession):
    result = await db.execute(
        select(Spread).where(Spread.id == spread_id, Spread.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Spread not found")

    service = SpreadService(db)
    try:
        ai_result = await service.generate_interpretation(spread_id)
        return AIResultResponse(
            response_text=ai_result.response_text,
            past=ai_result.past_interpretation,
            present=ai_result.present_interpretation,
            future=ai_result.future_interpretation,
            advice=ai_result.advice,
            conclusion=ai_result.conclusion,
            generation_time_ms=ai_result.generation_time_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {e}")


@router.post("/spreads/{spread_id}/share", response_model=ShareMessageResponse)
async def prepare_spread_share(spread_id: int, user: RequireTermsUser, db: DbSession):
    """Prepare a message for native Telegram shareMessage() in the Mini App."""
    try:
        msg_id = await prepare_spread_share_message(db, spread_id, user)
        return ShareMessageResponse(share_message_id=msg_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Share prepare failed: {e}") from e


@router.get("/spreads/{spread_id}", response_model=SpreadDetailResponse)
async def get_spread(spread_id: int, user: CurrentUser, db: DbSession):
    result = await db.execute(
        select(Spread)
        .options(
            selectinload(Spread.cards).selectinload(SpreadCard.card),
            selectinload(Spread.category),
            selectinload(Spread.ai_result),
        )
        .where(Spread.id == spread_id, Spread.user_id == user.id)
    )
    spread = result.scalar_one_or_none()
    if not spread:
        raise HTTPException(status_code=404, detail="Spread not found")

    response = _spread_to_response(spread)
    ai_data = None
    if spread.ai_result:
        ai_data = AIResultResponse(
            response_text=spread.ai_result.response_text,
            past=spread.ai_result.past_interpretation,
            present=spread.ai_result.present_interpretation,
            future=spread.ai_result.future_interpretation,
            advice=spread.ai_result.advice,
            conclusion=spread.ai_result.conclusion,
            generation_time_ms=spread.ai_result.generation_time_ms,
        )
    return SpreadDetailResponse(**response.model_dump(), ai_result=ai_data)


@router.get("/history", response_model=list[HistoryItemResponse])
async def get_history(user: CurrentUser, db: DbSession):
    service = SpreadService(db)
    is_premium = await service._is_premium(user.id)
    spreads = await service.get_spread_history(user.id, is_premium)

    fav_result = await db.execute(select(Favorite.spread_id).where(Favorite.user_id == user.id))
    fav_ids = set(fav_result.scalars().all())

    items = []
    for s in spreads:
        cards = [sc.card.name for sc in sorted(s.cards, key=lambda x: x.order)]
        items.append(
            HistoryItemResponse(
                id=s.id,
                category_name=s.category.name,
                category_emoji=s.category.emoji,
                cards=cards,
                situation=s.situation,
                conclusion=s.ai_result.conclusion if s.ai_result else None,
                created_at=s.created_at.isoformat(),
                is_favorite=s.id in fav_ids,
            )
        )
    return items


@router.post("/favorites")
async def add_favorite(body: FavoriteRequest, user: CurrentUser, db: DbSession):
    fav = Favorite(user_id=user.id, spread_id=body.spread_id)
    db.add(fav)
    return {"status": "ok"}


@router.delete("/favorites/{spread_id}")
async def remove_favorite(spread_id: int, user: CurrentUser, db: DbSession):
    result = await db.execute(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.spread_id == spread_id)
    )
    fav = result.scalar_one_or_none()
    if fav:
        await db.delete(fav)
    return {"status": "ok"}


_PLAN_TITLES = {
    "month_1": "Подписка Мир Таро — 1 месяц",
    "month_3": "Подписка Мир Таро — 3 месяца",
    "month_6": "Подписка Мир Таро — 6 месяцев",
}


@router.post("/payments", response_model=PaymentResponse)
async def create_payment(body: PaymentCreateRequest, user: RequireTermsUser, db: DbSession):
    service = PaymentService(db)

    if body.payment_type == "single_spread":
        payment = await service.create_payment(
            user, PaymentType.SINGLE_SPREAD, service.get_single_spread_price()
        )
        title = "Разовый расклад Мир Таро"
        description = "Один дополнительный расклад Таро сверх дневного лимита."
    elif body.payment_type == "subscription" and body.plan:
        plan = SubscriptionPlan(body.plan)
        payment = await service.create_payment(
            user, PaymentType.SUBSCRIPTION, service.get_subscription_price(plan), plan
        )
        title = _PLAN_TITLES.get(body.plan, "Подписка Мир Таро")
        description = "Premium-доступ: 15 раскладов в сутки, полная история, все функции."
    else:
        raise HTTPException(status_code=400, detail="Invalid payment request")

    invoice_link: str | None = None
    try:
        invoice_link = await service.create_invoice_link(
            title=title,
            description=description,
            payload=str(payment.id),
            stars=payment.stars_amount,
        )
    except Exception as e:  # noqa: BLE001 — do not fail the whole request on invoice error
        raise HTTPException(status_code=502, detail=f"Не удалось создать счёт Telegram Stars: {e}")

    return PaymentResponse(
        id=payment.id,
        payment_type=payment.payment_type.value,
        stars_amount=payment.stars_amount,
        status=payment.status.value,
        plan=payment.plan.value if payment.plan else None,
        invoice_link=invoice_link,
    )


@router.post("/payments/telegram/confirm")
async def confirm_stars_payment(body: StarsConfirmRequest, db: DbSession):
    """Internal endpoint called by the bot after a successful Stars payment."""
    if body.secret != settings.internal_api_secret:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        payment_id = int(body.payload)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid payload")

    service = PaymentService(db)
    payment = await service.confirm_payment_by_id(payment_id, body.telegram_payment_charge_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"status": "confirmed", "payment_id": payment.id}


@router.post("/payments/confirm")
async def confirm_payment(
    user: CurrentUser,
    db: DbSession,
    telegram_payment_id: str,
):
    service = PaymentService(db)
    payment = await service.confirm_payment(telegram_payment_id, user.id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"status": "confirmed", "payment_id": payment.id}


def _spread_to_response(spread: Spread) -> SpreadResponse:
    cards = [
        CardResponse(
            id=sc.card.id,
            slug=sc.card.slug,
            name=sc.card.name,
            position=sc.position,
            is_reversed=sc.is_reversed,
            image_url=sc.card.image_url,
        )
        for sc in sorted(spread.cards, key=lambda x: x.order)
    ]
    return SpreadResponse(
        id=spread.id,
        category_slug=spread.category.slug,
        category_name=spread.category.name,
        situation=spread.situation,
        emotion=spread.emotion,
        status=spread.status.value,
        cards=cards,
        created_at=spread.created_at.isoformat(),
    )
