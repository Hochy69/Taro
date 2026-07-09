import asyncio
import logging

from app.bot_setup import setup_bot_menu
from app.handlers.commands import bot, dp

logging.basicConfig(level=logging.INFO)


async def main():
    # Drop third-party webhooks (e.g. if bot was linked to ControllerBot by mistake).
    await bot.delete_webhook(drop_pending_updates=False)
    await setup_bot_menu(bot)
    logging.info("Bot menu set to commands list")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
