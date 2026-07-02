"""Seed database with initial tarot cards and categories."""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select

from app.infrastructure.database.models import Category, TarotCard, TarotDeck, TarotMeaning
from app.infrastructure.database.seed_data import CATEGORIES, GENERAL_MEANINGS, MAJOR_ARCANA
from app.infrastructure.database.session import async_session


async def seed():
    async with async_session() as session:
        existing = await session.execute(select(Category).limit(1))
        if existing.scalar_one_or_none():
            print("Database already seeded")
            return

        for slug, name, emoji, order in CATEGORIES:
            session.add(Category(slug=slug, name=name, emoji=emoji, sort_order=order))

        deck = TarotDeck(slug="rider-waite", name="Rider-Waite", is_default=True)
        session.add(deck)
        await session.flush()

        for slug, name, arcana, suit, number in MAJOR_ARCANA:
            card = TarotCard(
                deck_id=deck.id,
                slug=slug,
                name=name,
                arcana=arcana,
                suit=suit,
                number=number,
                image_url=f"/cards/{slug}.jpg",
            )
            session.add(card)
            await session.flush()

            if slug in GENERAL_MEANINGS:
                upright, advice = GENERAL_MEANINGS[slug]
                for pos in ["past", "present", "future", "upright"]:
                    session.add(
                        TarotMeaning(
                            card_id=card.id,
                            category_slug="general",
                            position=pos,
                            keywords=upright.split(",")[0],
                            meaning=upright,
                            advice=advice,
                        )
                    )
                session.add(
                    TarotMeaning(
                        card_id=card.id,
                        category_slug="general",
                        position="reversed",
                        meaning=f"Перевёрнутая {name}: внутренние блоки мешают проявлению энергии карты.",
                        advice="Обратите внимание на то, что вы избегаете.",
                    )
                )

        await session.commit()
        print("Database seeded successfully")


if __name__ == "__main__":
    asyncio.run(seed())
