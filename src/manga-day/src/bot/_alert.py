import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramNotFound
from loguru import logger

from ..core.abstract.alert import BaseAlert, LEVEL
from ..core import config


class BotAlert(BaseAlert):
    """Логика уведомлений бота"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def alert(self, message: str, level: LEVEL):
        """Отправляет сообщение в чаты администраторов бота"""
        message += f"\n\nУровень: <b>{level}</b>"

        async def send(chat_id: int):
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                )
            except TelegramNotFound:
                logger.warning(f"Чат {chat_id} не найден")

        await asyncio.gather(
            *[asyncio.create_task(send(chat_id)) for chat_id in config.bot.admins],
            return_exceptions=True,
        )

        return True
