"""Partner / ad acquisition attribution (first-touch)."""

from __future__ import annotations

import re

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.admin_stats_service import (
    TEST_TELEGRAM_IDS,
    _is_production_user,
    _is_real_payment,
)
from app.infrastructure.database.models import (
    AcquisitionPending,
    Payment,
    PaymentStatus,
    User,
)

_SOURCE_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,62}$")


def normalize_acquisition_source(raw: str | None) -> str | None:
    """Normalize deep-link payload. Referrals (`ref_`) are handled separately."""
    if not raw:
        return None
    source = raw.strip().lower()
    if not source or source.startswith("ref_"):
        return None
    source = source[:64]
    if not _SOURCE_RE.match(source):
        return None
    return source


class AttributionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_pending(self, telegram_id: int, raw_source: str) -> str | None:
        source = normalize_acquisition_source(raw_source)
        if not source:
            return None
        existing = await self.session.get(AcquisitionPending, telegram_id)
        if existing:
            existing.source = source
        else:
            self.session.add(AcquisitionPending(telegram_id=telegram_id, source=source))
        await self.session.flush()
        return source

    async def apply_to_user(self, user: User, start_param: str | None = None) -> str | None:
        """First-touch attribution from WebApp start_param or pending bot /start."""
        if user.acquisition_source:
            await self._clear_pending(user.telegram_id)
            return user.acquisition_source

        source = normalize_acquisition_source(start_param)
        if not source:
            pending = await self.session.get(AcquisitionPending, user.telegram_id)
            if pending:
                source = pending.source

        if source:
            user.acquisition_source = source
            await self.session.flush()

        await self._clear_pending(user.telegram_id)
        return source

    async def _clear_pending(self, telegram_id: int) -> None:
        await self.session.execute(
            delete(AcquisitionPending).where(AcquisitionPending.telegram_id == telegram_id)
        )

    async def partner_stats(self) -> list[dict]:
        users_q = (
            select(
                User.acquisition_source.label("source"),
                func.count(User.id).label("users_count"),
            )
            .where(
                User.acquisition_source.is_not(None),
                _is_production_user(),
            )
            .group_by(User.acquisition_source)
        )
        users_rows = (await self.session.execute(users_q)).all()

        pay_q = (
            select(
                User.acquisition_source.label("source"),
                func.count(func.distinct(Payment.user_id)).label("paying_users"),
                func.coalesce(func.sum(Payment.stars_amount), 0).label("revenue_stars"),
            )
            .join(Payment, Payment.user_id == User.id)
            .where(
                User.acquisition_source.is_not(None),
                _is_production_user(),
                Payment.status == PaymentStatus.COMPLETED,
                _is_real_payment(),
            )
            .group_by(User.acquisition_source)
        )
        pay_map = {
            row.source: {
                "paying_users": int(row.paying_users),
                "revenue_stars": int(row.revenue_stars),
            }
            for row in (await self.session.execute(pay_q)).all()
        }

        pending_q = (
            select(
                AcquisitionPending.source,
                func.count().label("pending_count"),
            )
            .where(AcquisitionPending.telegram_id.notin_(TEST_TELEGRAM_IDS))
            .group_by(AcquisitionPending.source)
        )
        pending_map = {
            row.source: int(row.pending_count)
            for row in (await self.session.execute(pending_q)).all()
        }

        sources = sorted(
            {*(r.source for r in users_rows), *pay_map.keys(), *pending_map.keys()}
        )
        users_map = {r.source: int(r.users_count) for r in users_rows}

        result = []
        for source in sources:
            revenue = pay_map.get(source, {}).get("revenue_stars", 0)
            result.append(
                {
                    "source": source,
                    "link": f"https://t.me/best1tarolog_bot?start={source}",
                    "users_count": users_map.get(source, 0),
                    "pending_starts": pending_map.get(source, 0),
                    "paying_users": pay_map.get(source, {}).get("paying_users", 0),
                    "revenue_stars": revenue,
                    "partner_share_35pct": int(round(revenue * 0.35)),
                }
            )
        result.sort(key=lambda x: (x["revenue_stars"], x["users_count"]), reverse=True)
        return result
