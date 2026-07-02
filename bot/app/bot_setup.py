"""Telegram bot menu: command list instead of direct WebApp button."""

from aiogram import Bot
from aiogram.types import BotCommand, MenuButtonCommands

BOT_COMMANDS: list[BotCommand] = [
    BotCommand(command="start", description="Начать работу с ботом"),
    BotCommand(command="app", description="Открыть мини-приложение"),
    BotCommand(command="premium", description="Premium подписка"),
    BotCommand(command="invite", description="Пригласить друга"),
    BotCommand(command="history", description="История раскладов"),
    BotCommand(command="help", description="Справка по командам"),
]


async def setup_bot_menu(bot: Bot) -> None:
    await bot.set_my_commands(BOT_COMMANDS)
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands(text="Меню"))
