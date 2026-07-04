"""Telegram bot menu: WebApp button + command list."""

from aiogram import Bot
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from app.webapp_url import get_webapp_url

BOT_COMMANDS: list[BotCommand] = [
    BotCommand(command="start", description="Начать работу с ботом"),
    BotCommand(command="app", description="Открыть мини-приложение"),
    BotCommand(command="card", description="Карта дня"),
    BotCommand(command="premium", description="Premium подписка"),
    BotCommand(command="invite", description="Пригласить друга"),
    BotCommand(command="history", description="История раскладов"),
    BotCommand(command="help", description="Справка по командам"),
]


async def setup_bot_menu(bot: Bot) -> None:
    await bot.set_my_commands(BOT_COMMANDS)
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="🔮 Мир Таро",
            web_app=WebAppInfo(url=get_webapp_url()),
        )
    )