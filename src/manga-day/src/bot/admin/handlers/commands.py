from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from ....core.manager.spider import SpiderManager
from .._text import GREETING, HELP


class CommandsHandler:
    """Обработчик команд Telegram-бота для управления парсингом.

    Инициализирует маршрутизатор и регистрирует обработчики команд.
    Использует SpiderManager для управления жизненным циклом парсера.

    Args:
        spider_manager (SpiderManager): Экземпляр менеджера парсинга для управления запуском, остановкой и получением статуса.

    Attributes:
        router (Router): Маршрутизатор aiogram для регистрации обработчиков сообщений.
        spider_manager (SpiderManager): Ссылка на менеджер парсинга.
    """

    def __init__(self, spider_manager: SpiderManager):
        """Инициализация обработчика команд.

        Создаёт экземпляр роутера и регистрирует обработчики команд.

        Args:
            spider_manager (SpiderManager): Менеджер для управления процессом парсинга.
        """
        self.router = Router()
        self.spider_manager = spider_manager
        self.register_handlers()

    def register_handlers(self):
        """Регистрирует все обработчики команд в роутере.

        Обрабатывает следующие команды:
        - /start
        - /help
        - /start_parsing
        - /stop_parsing
        - /stop_spider
        - /start_spider
        - /status
        """
        self.router.message.register(self.start, Command("start"))
        self.router.message.register(self.help, Command("help"))
        self.router.message.register(self.start_parsing, Command("start_parsing"))
        self.router.message.register(self.stop_parsing, Command("stop_parsing"))
        self.router.message.register(self.stop_spider, Command("stop_spider"))
        self.router.message.register(self.start_spider, Command("start_spider"))
        self.router.message.register(self.status, Command("status"))

    async def start(self, message: Message):
        """Отправляет приветственное сообщение при получении команды /start.

        Args:
            message (Message): Входящее сообщение от пользователя.
        """
        await message.answer(GREETING)

    async def help(self, message: Message):
        """Отправляет справочное сообщение при получении команды /help.

        Args:
            message (Message): Входящее сообщение от пользователя.
        """
        await message.answer(HELP)

    async def start_parsing(self, message: Message):
        """Запускает процесс парсинга по команде /start_parsing.

        Отправляет уведомление о попытке запуска,
        затем делегирует выполнение SpiderManager.

        Args:
            message (Message): Входящее сообщение от пользователя.

        Raises:
            Исключения могут быть выброшены методом start_parsing() SpiderManager.
        """
        await message.answer("Попытка начать парсинг")
        await self.spider_manager.start_full_parsing()

    async def stop_parsing(self, message: Message):
        """Останавливает процесс парсинга по команде /stop_parsing.

        Отправляет уведомление о попытке остановки,
        затем делегирует выполнение SpiderManager.

        Args:
            message (Message): Входящее сообщение от пользователя.

        Raises:
            Исключения могут быть выброшены методом stop_parsing() SpiderManager.
        """
        await message.answer("Попытка остановить парсинг")
        await self.spider_manager.stop_all_spider()

    async def stop_spider(self, message: Message):
        """Останавливает спайдера по команде /stop [spider_name].

        Args:
            message (Message): Входящее сообщение от пользователя.
        """
        try:
            _, spider_name = message.text.split()
            try:
                await self.spider_manager.starter.stop_spider(spider_name)
            except KeyError:
                await message.answer(f"Спайдер {spider_name} не найден.")
        except ValueError:
            await message.answer(
                "Неверный формат команды. Используйте: /stop_spider [spider_name]"
            )

    async def start_spider(self, message: Message):
        """Запускает спайдер по команде /start [spider_name].

        Args:
            message (Message): Входящее сообщение от пользователя.
        """
        try:
            _, spider_name = message.text.split()
            try:
                await self.spider_manager.starter.start_spider(spider_name)
            except KeyError:
                await message.answer("Спайдер не найден.")
        except ValueError:
            await message.answer(
                "Неверный формат команды. Используйте: /start_spider [spider_name]"
            )

    async def status(self, message: Message):
        """Отправляет текущий статус парсера по команде /status.

        Args:
            message (Message): Входящее сообщение от пользователя.

        Raises:
            AttributeError: Если spider_manager не имеет атрибута status.
        """
        await message.answer("\n".join(str(x) for x in self.spider_manager.status))
