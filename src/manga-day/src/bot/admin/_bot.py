from typing import TypedDict, Unpack
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from ...core import config
from ...core.manager.spider import SpiderManager
from .._alert import BotAlert
from .._tools import get_router
from .handlers.commands import CommandsHandler
from .middleware.admins import AdminMiddleware


class BotConfig(TypedDict):
    """Конфигурация для инициализации бота.

    Args:
        spider (SpiderManager): Экземпляр менеджера парсинга.
        token (str | None, optional): Токен Telegram-бота. По умолчанию берётся из конфига.
    """

    spider: SpiderManager
    token: str | None


async def set_command(bot: Bot):
    """Регистрирует список команд бота в интерфейсе Telegram.

    Отображает пользователю доступные команды с описаниями.

    Args:
        bot (Bot): Экземпляр Telegram-бота.

    Returns:
        None
    """
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="help", description="Помощь"),
            BotCommand(command="start_parsing", description="Запустить парсинг"),
            BotCommand(command="stop_parsing", description="Остановить парсинг"),
            BotCommand(
                command="stop_spider", description="Остановить парсинг выбранного паука"
            ),
            BotCommand(
                command="start_spider", description="Запустить парсинг выбранного паука"
            ),
            BotCommand(command="status", description="Статус парсинга"),
        ]
    )


@asynccontextmanager
async def setup_bot(**kwargs: Unpack[BotConfig]):
    """Асинхронный контекстный менеджер для настройки и запуска Telegram-бота.

    Инициализирует бота, диспетчер, регистрирует обработчики и мидлвари.
    При выходе из контекста корректно завершает работу бота.

    Args:
        **kwargs: Параметры конфигурации, см. BotConfig.

    Yields:
        tuple[Bot, Dispatcher]: Экземпляры бота и диспетчера.

    Raises:
        AttributeError: Если не передан spider.
        TypeError: Если spider не является экземпляром SpiderManager.
    """
    spider = kwargs.get("spider")
    token = kwargs.get("token") or config.bot.api_key

    if spider is None:
        raise AttributeError("SpiderManager не указан")
    elif not isinstance(spider, SpiderManager):
        raise TypeError("SpiderManager должен быть экземпляром SpiderManager")

    dp = None
    try:
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        async with Bot(
            token=token, default=DefaultBotProperties(parse_mode="HTML")
        ) as bot:
            logger.info("Инициализация бота...")
            await set_command(bot)

            spider.alert.add_alert(BotAlert(bot))
            handler = CommandsHandler(spider_manager=spider)

            dp.include_routers(handler.router, get_router())
            dp.message.middleware(AdminMiddleware(config.bot.admins))

            logger.info("Бот инициализирован")
            yield bot, dp
    finally:
        if dp is not None:
            try:
                await dp.stop_polling()
            except RuntimeError:
                pass
        await spider.alert.alert("<b>Бот прекратил свою работу</b>", "warning")
        logger.info("Бот остановлен")


async def start_bot(**kwargs: Unpack[BotConfig]):
    """Запускает бота в режиме long polling.

    Использует контекстный менеджер setup_bot для инициализации.
    После запуска начинает получать обновления от Telegram.

    Args:
        **kwargs: Параметры конфигурации, см. BotConfig.

    Returns:
        None

    Raises:
        Исключения могут быть выброшены setup_bot или при работе dp.start_polling().
    """
    async with setup_bot(**kwargs) as (bot, dp):
        logger.success(f"{await bot.get_my_name()} - Бот запущен")
        await dp.start_polling(bot)
