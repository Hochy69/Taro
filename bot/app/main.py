import asyncio
import logging

from app.bot_setup import setup_bot_menu
from app.handlers.commands import bot, dp

logging.basicConfig(level=logging.INFO)


async def main():
    await setup_bot_menu(bot)
    logging.info("Bot menu set to commands list")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
