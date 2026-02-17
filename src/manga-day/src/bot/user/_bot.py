from typing import TypedDict, Unpack
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from ...core import config
from ...core.manager import MangaManager, AlertManager
from ...core.service import PDFService
from .._tools import get_router
from .handler import CommandsHandler


class BotConfig(TypedDict):
    """Конфигурация для инициализации бота.

    Args:
        manager (MangaManager): Экземпляр менеджера манги.
        pdf_service (PDFService): Экземпляр для работы с PDF.
        alert (AlertManager): Экземпляр менеджера оповещений.
        save_path (str | None, optional): Путь для хранение PDF - файлов
        token (str | None, optional): Токен Telegram-бота. По умолчанию берётся из конфига.
    """

    manager: MangaManager
    pdf_service: PDFService
    alert: AlertManager
    save_path: str | None
    token: str | None


async def set_command(bot: Bot):
    """Регистрирует список команд бота в интерфейсе Telegram.

    Отображает пользователю доступные команды с описаниями.

    Args:
        bot (Bot): Экземпляр Telegram-бота.
    """
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="help", description="Помощь"),
            BotCommand(command="download", description="Скачивает мангу по SKU"),
        ]
    )


@asynccontextmanager
async def setup_user(**kwargs: Unpack[BotConfig]):
    """Асинхронный контекстный менеджер для настройки и запуска Telegram-бота.

    Инициализирует бота, диспетчер, регистрирует обработчики и мидлвари.
    При выходе из контекста корректно завершает работу бота.

    Args:
        **kwargs: Параметры конфигурации, см. BotConfig.

    Yields:
        tuple[Bot, Dispatcher]: Экземпляры бота и диспетчера.

    Raises:
        AttributeError: Если не передан manager.
        TypeError: Если manager не является экземпляром MangaManager.
    """
    alert = kwargs.get("alert")
    pdf = kwargs.get("pdf_service")
    save_path = kwargs.get("save_path")

    manager = kwargs.get("manager")
    token = kwargs.get("token") or config.user_bot.api_key

    if manager is None:
        raise AttributeError("MangaManager не указан")
    elif not isinstance(manager, MangaManager):
        raise TypeError("MangaManager должен быть экземпляром MangaManager")

    dp = None
    try:
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        async with Bot(
            token=token, default=DefaultBotProperties(parse_mode="HTML")
        ) as bot:
            logger.info("Инициализация бота...")
            await set_command(bot)

            handler = CommandsHandler(manager=manager, pdf=pdf, save_path=save_path)

            dp.include_routers(handler.router, get_router())

            logger.info("Бот инициализирован")
            yield bot, dp
    finally:
        if dp is not None:
            try:
                await dp.stop_polling()
            except RuntimeError:
                pass

        await alert.alert("<b>USER - Бот прекратил свою работу</b>", "warning")
        logger.info("USER - Бот остановлен")


async def start_user(**kwargs: Unpack[BotConfig]):
    async with setup_user(**kwargs) as (bot, dp):
        logger.success(f"{await bot.get_my_name()} - Бот запущен")
        await dp.start_polling(bot)
