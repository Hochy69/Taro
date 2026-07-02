"""Referral program: invite friends, both get a bonus spread."""

from __future__ import annotations

import logging
import secrets

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.database.models import Referral, ReferralPending, User, UserLimit

logger = logging.getLogger(__name__)

REF_PREFIX = "ref_"


def _generate_code() -> str:
    return secrets.token_hex(4).upper()


def _extract_code(raw: str | None) -> str | None:
    if not raw:
        return None
    value = raw.strip()
    if value.lower().startswith(REF_PREFIX):
        value = value[len(REF_PREFIX) :]
    return value.upper() if value else None


async def grant_bonus_spreads(session: AsyncSession, user_id: int, count: int = 1) -> None:
    """Add bonus spreads to a user (same mechanism as paid single-spread purchase)."""
    if count <= 0:
        return
    result = await session.execute(select(UserLimit).where(UserLimit.user_id == user_id))
    limit = result.scalar_one_or_none()
    if limit:
        limit.bonus_spreads += count
    else:
        session.add(UserLimit(user_id=user_id, bonus_spreads=count))


class ReferralService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ensure_referral_code(self, user: User) -> str:
        if user.referral_code:
            return user.referral_code

        for _ in range(8):
            code = _generate_code()
            existing = await self.session.execute(
                select(User.id).where(User.referral_code == code)
            )
            if existing.scalar_one_or_none() is None:
                user.referral_code = code
                await self.session.flush()
                return code

        raise RuntimeError("Failed to generate unique referral code")

    def build_link(self, code: str) -> str:
        username = settings.telegram_bot_username.strip().lstrip("@")
        return f"https://t.me/{username}?start={REF_PREFIX}{code}"

    async def get_info(self, user: User) -> dict:
        code = await self.ensure_referral_code(user)
        count_result = await self.session.execute(
            select(func.count()).select_from(Referral).where(Referral.referrer_id == user.id)
        )
        invites_count = int(count_result.scalar_one() or 0)
        return {
            "code": code,
            "link": self.build_link(code),
            "invites_count": invites_count,
            "bonus_earned": invites_count,
        }

    async def save_pending(self, telegram_id: int, referral_code: str) -> None:
        code = _extract_code(referral_code)
        if not code:
            return

        existing = await self.session.execute(
            select(ReferralPending).where(ReferralPending.telegram_id == telegram_id)
        )
        pending = existing.scalar_one_or_none()
        if pending:
            pending.referral_code = code
        else:
            self.session.add(ReferralPending(telegram_id=telegram_id, referral_code=code))
        await self.session.flush()

    async def process_signup(
        self,
        new_user: User,
        start_param: str | None = None,
    ) -> bool:
        """Apply referral on first signup. Returns True if a referral was rewarded."""
        if new_user.referred_by_id is not None:
            return False

        code = _extract_code(start_param)
        if not code:
            pending_result = await self.session.execute(
                select(ReferralPending).where(ReferralPending.telegram_id == new_user.telegram_id)
            )
            pending = pending_result.scalar_one_or_none()
            if pending:
                code = pending.referral_code

        if not code:
            return False

        referrer_result = await self.session.execute(
            select(User).where(User.referral_code == code)
        )
        referrer = referrer_result.scalar_one_or_none()
        if not referrer or referrer.id == new_user.id:
            await self._clear_pending(new_user.telegram_id)
            return False

        dup = await self.session.execute(
            select(Referral.id).where(Referral.referee_id == new_user.id)
        )
        if dup.scalar_one_or_none() is not None:
            return False

        new_user.referred_by_id = referrer.id
        self.session.add(Referral(referrer_id=referrer.id, referee_id=new_user.id))
        await grant_bonus_spreads(self.session, referrer.id, 1)
        await grant_bonus_spreads(self.session, new_user.id, 1)
        await self._clear_pending(new_user.telegram_id)
        await self.session.flush()

        logger.info(
            "Referral completed: referrer=%s referee=%s",
            referrer.id,
            new_user.id,
        )
        return True

    async def _clear_pending(self, telegram_id: int) -> None:
        result = await self.session.execute(
            select(ReferralPending).where(ReferralPending.telegram_id == telegram_id)
        )
        pending = result.scalar_one_or_none()
        if pending:
            await self.session.delete(pending)
