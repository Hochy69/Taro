import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.services.tarot_ai_service import TarotAIService
from app.core.config import settings
from app.infrastructure.database.models import (
    AIResult,
    AnalyticsEvent,
    Category,
    Profile,
    Spread,
    SpreadCard,
    SpreadStatus,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    TarotCard,
    TarotMeaning,
    User,
    UserLimit,
)


class SpreadService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.ai_service = TarotAIService()

    async def get_user_with_profile(self, user_id: int) -> User | None:
        result = await self.session.execute(
            select(User).options(selectinload(User.profile)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def _ensure_limit_record(self, user: User) -> UserLimit:
        limit_record = user.limits
        if not limit_record:
            limit_record = UserLimit(user_id=user.id, last_reset_date=date.today())
            self.session.add(limit_record)
            await self.session.flush()
            user.limits = limit_record
        return limit_record

    def _reset_window_if_needed(self, limit_record: UserLimit, is_premium: bool) -> None:
        """Premium: daily reset. Free: reset once per rolling N-day period."""
        today = date.today()
        if is_premium:
            if limit_record.last_reset_date < today:
                limit_record.daily_spreads_used = 0
                limit_record.last_reset_date = today
            return
        period = timedelta(days=settings.free_spread_period_days)
        if today - limit_record.last_reset_date >= period:
            limit_record.daily_spreads_used = 0
            limit_record.last_reset_date = today

    def _base_limit(self, is_premium: bool) -> int:
        if is_premium:
            return settings.premium_daily_spreads
        return settings.free_spreads_per_period

    async def check_daily_limit(self, user: User) -> tuple[bool, int, int]:
        """Returns (can_spread, used, base_limit).

        Free users get ``free_spreads_per_period`` spreads per rolling
        ``free_spread_period_days`` window. Purchased single spreads
        (``bonus_spreads``) are always usable on top of that.
        """
        # Admins have permanent, unlimited access to everything.
        if getattr(user, "is_admin", False):
            used = user.limits.daily_spreads_used if user.limits else 0
            return True, used, 999999

        is_premium = await self._is_premium(user.id)
        limit_record = await self._ensure_limit_record(user)
        self._reset_window_if_needed(limit_record, is_premium)

        base_limit = self._base_limit(is_premium)
        used = limit_record.daily_spreads_used
        can_spread = used < base_limit or limit_record.bonus_spreads > 0
        return can_spread, used, base_limit

    async def _is_premium(self, user_id: int) -> bool:
        # Admins are always treated as premium (full access forever).
        is_admin = await self.session.execute(
            select(User.is_admin).where(User.id == user_id)
        )
        if is_admin.scalar_one_or_none():
            return True

        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.expires_at > now,
                Subscription.plan != SubscriptionPlan.FREE,
            )
        )
        return result.scalar_one_or_none() is not None

    async def is_premium(self, user_id: int) -> bool:
        return await self._is_premium(user_id)

    async def _refund_spread_quota(self, user: User, spread: Spread) -> None:
        if user.is_admin or spread.quota_from_bonus is None:
            return
        limit_record = await self._ensure_limit_record(user)
        if spread.quota_from_bonus:
            limit_record.bonus_spreads += 1
        elif limit_record.daily_spreads_used > 0:
            limit_record.daily_spreads_used -= 1
        spread.quota_from_bonus = None
        await self.session.flush()

    async def draw_cards(self, count: int = 3) -> list[TarotCard]:
        result = await self.session.execute(select(TarotCard))
        all_cards = list(result.scalars().all())
        if len(all_cards) < count:
            raise ValueError("Not enough cards in deck")
        return random.sample(all_cards, count)

    async def get_card_meaning(
        self, card_id: int, category_slug: str, position: str, is_reversed: bool
    ) -> str:
        pos = "reversed" if is_reversed else position
        result = await self.session.execute(
            select(TarotMeaning).where(
                TarotMeaning.card_id == card_id,
                TarotMeaning.category_slug.in_([category_slug, "general"]),
                TarotMeaning.position.in_([pos, position, "upright"]),
            )
        )
        meanings = result.scalars().all()
        if meanings:
            for m in meanings:
                if m.category_slug == category_slug and m.position == pos:
                    return m.meaning
            return meanings[0].meaning
        return "Карта несёт важное послание для вашей ситуации."

    async def create_spread(
        self,
        user: User,
        category_slug: str,
        situation: str,
        emotion: str,
        profile_data: dict | None = None,
    ) -> Spread:
        limit_record = await self._ensure_limit_record(user)
        consume_from_bonus = False
        charged_quota = False

        if not user.is_admin:
            is_premium = await self._is_premium(user.id)
            self._reset_window_if_needed(limit_record, is_premium)
            base_limit = self._base_limit(is_premium)

            if limit_record.daily_spreads_used < base_limit:
                consume_from_bonus = False
            elif limit_record.bonus_spreads > 0:
                consume_from_bonus = True
            else:
                raise PermissionError("Daily spread limit reached")

        cat_result = await self.session.execute(
            select(Category).where(Category.slug == category_slug)
        )
        category = cat_result.scalar_one_or_none()
        if not category:
            raise ValueError(f"Category not found: {category_slug}")

        if profile_data:
            profile = user.profile or Profile(user_id=user.id)
            if not user.profile:
                self.session.add(profile)
            profile.name = profile_data.get("name", profile.name)
            if profile_data.get("birth_date"):
                profile.birth_date = profile_data["birth_date"]
            if profile_data.get("birth_time") is not None:
                profile.birth_time = profile_data.get("birth_time") or None
            if profile_data.get("birth_city") is not None:
                profile.birth_city = profile_data.get("birth_city") or None
            if profile_data.get("gender") is not None:
                profile.gender = profile_data.get("gender") or None
            profile.zodiac_sign = profile_data.get("zodiac_sign", profile.zodiac_sign)
            profile.last_category_slug = category_slug
            if profile.birth_date:
                from app.application.services.geocoding_service import resolve_city
                from app.application.services.lunar_service import get_lunar_day

                profile.lunar_birth_day = get_lunar_day(profile.birth_date)
                if profile.birth_city:
                    lat, lon, tz, _ = resolve_city(profile.birth_city)
                    profile.birth_lat = lat
                    profile.birth_lon = lon
                    profile.birth_timezone = tz

        if not user.is_admin:
            if consume_from_bonus:
                limit_record.bonus_spreads -= 1
            else:
                limit_record.daily_spreads_used += 1
            charged_quota = True

        spread = Spread(
            user_id=user.id,
            category_id=category.id,
            situation=situation,
            emotion=emotion,
            status=SpreadStatus.PENDING,
            quota_from_bonus=consume_from_bonus if charged_quota else None,
        )
        self.session.add(spread)
        await self.session.flush()

        cards = await self.draw_cards(3)
        positions = ["past", "present", "future"]
        for i, (card, position) in enumerate(zip(cards, positions)):
            is_reversed = random.random() < 0.3
            spread_card = SpreadCard(
                spread_id=spread.id,
                card_id=card.id,
                position=position,
                is_reversed=is_reversed,
                order=i,
            )
            self.session.add(spread_card)

        self.session.add(
            AnalyticsEvent(event_type="spread_created", user_id=user.id, category_id=category.id)
        )
        await self.session.flush()
        return spread

    async def generate_interpretation(self, spread_id: int) -> AIResult:
        result = await self.session.execute(
            select(Spread)
            .options(
                selectinload(Spread.cards).selectinload(SpreadCard.card),
                selectinload(Spread.category),
                selectinload(Spread.user).selectinload(User.profile),
                selectinload(Spread.ai_result),
            )
            .where(Spread.id == spread_id)
        )
        spread = result.scalar_one_or_none()
        if not spread:
            raise ValueError("Spread not found")

        # Идемпотентность: если интерпретация уже создана — возвращаем её,
        # не плодя дубликаты (spread_id в AIResult уникален).
        if spread.ai_result is not None:
            return spread.ai_result

        spread.status = SpreadStatus.GENERATING
        await self.session.flush()

        try:
            profile = spread.user.profile
            cards_data = []
            for sc in sorted(spread.cards, key=lambda x: x.order):
                meaning = await self.get_card_meaning(
                    sc.card_id, spread.category.slug, sc.position, sc.is_reversed
                )
                cards_data.append({
                    "position": {"past": "Прошлое", "present": "Настоящее", "future": "Будущее"}[sc.position],
                    "name": sc.card.name,
                    "is_reversed": sc.is_reversed,
                    "meaning": meaning,
                })

            ai_response = await self.ai_service.generate_reading(
                name=profile.name if profile else "Дорогой друг",
                birth_date=profile.birth_date if profile else None,
                zodiac_sign=profile.zodiac_sign if profile else None,
                category=spread.category.name,
                situation=spread.situation or "",
                emotion=spread.emotion or "",
                cards=cards_data,
                category_slug=spread.category.slug,
            )

            provider_name = "template" if settings.template_only else settings.ai_provider
            model_name = "local" if settings.template_only else settings.ai_model

            ai_result = AIResult(
                spread_id=spread.id,
                provider=provider_name,
                model=model_name,
                prompt_tokens=ai_response.prompt_tokens,
                completion_tokens=ai_response.completion_tokens,
                generation_time_ms=ai_response.generation_time_ms,
                response_text=ai_response.text,
                past_interpretation=ai_response.past,
                present_interpretation=ai_response.present,
                future_interpretation=ai_response.future,
                advice=ai_response.advice,
                conclusion=ai_response.conclusion,
            )
            spread.status = SpreadStatus.COMPLETED
            self.session.add(ai_result)
            await self.session.flush()
            return ai_result
        except IntegrityError:
            await self.session.rollback()
            existing = await self.session.execute(
                select(AIResult).where(AIResult.spread_id == spread_id)
            )
            ai_result = existing.scalar_one_or_none()
            if ai_result:
                return ai_result
            raise
        except Exception:
            spread.status = SpreadStatus.FAILED
            await self._refund_spread_quota(spread.user, spread)
            await self.session.flush()
            raise

    async def get_spread_history(self, user_id: int, is_premium: bool) -> list[Spread]:
        query = (
            select(Spread)
            .options(
                selectinload(Spread.category),
                selectinload(Spread.cards).selectinload(SpreadCard.card),
                selectinload(Spread.ai_result),
            )
            .where(Spread.user_id == user_id, Spread.status == SpreadStatus.COMPLETED)
            .order_by(Spread.created_at.desc())
        )
        if not is_premium:
            query = query.limit(settings.free_history_limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
