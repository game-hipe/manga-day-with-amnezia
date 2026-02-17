"""Включение/выключние пауков"""

import asyncio

from typing import overload

from loguru import logger

from ._status import SpiderStatus, SpiderStatusEnum
from ..alert import AlertManager, LEVEL
from ...abstract.spider import BaseSpider


class SpiderStarter:
    def __init__(self, spiders: list[BaseSpider], alert: AlertManager | None = None):
        """Инцилизация системы старта пауков.

        Args:
            spiders (list[BaseSpider]): Пауки которых можно запустить
            alert (AlertManager | None, optional): Менеджер оповещений. Обычное состояние None
        """
        self.alert = alert
        self.spiders: dict[BaseSpider, None | asyncio.Task[None]] = {
            spider: None for spider in spiders
        }

    @overload
    async def start_spider(
        self, spider: BaseSpider, start_page: int | None = None
    ) -> None:
        """Начать работу паука.

        Args:
            spider (BaseSpider): Сам паук.
            start_page (int | None, optional): Параметр для выбора страницы для начало. Обычное состояние None
        """

    @overload
    async def start_spider(
        self, spider: type[BaseSpider], start_page: int | None = None
    ) -> None:
        """Начать работу паука.

        Args:
            spider (BaseSpider): Тип паука.
            start_page (int | None, optional): Параметр для выбора страницы для начало. Обычное состояние None
        """

    @overload
    async def start_spider(self, spider: str, start_page: int | None = None) -> None:
        """Начать работу паука.

        Args:
            spider (BaseSpider): Название паука.
            start_page (int | None, optional): Параметр для выбора страницы для начало. Обычное состояние None
        """

    @overload
    async def stop_spider(self, spider: BaseSpider) -> None:
        """Остановить работу паука

        Args:
            spider (BaseSpider): Сам паук.
        """

    @overload
    async def stop_spider(self, spider: type[BaseSpider]) -> None:
        """Остановить работу паука

        Args:
            spider (BaseSpider): Тип паука.
        """

    @overload
    async def stop_spider(self, spider: str) -> None:
        """Остановить работу паука

        Args:
            spider (BaseSpider): Название паука.
        """

    async def start_spider(
        self, spider: str | BaseSpider | type[BaseSpider], start_page: int | None = None
    ) -> SpiderStatus:
        """Начать работу паука.

        Args:
            spider (str | BaseSpider): Паук, либо название паука.
            start_page (int | None, optional): Параметр для выбора страницы для начало. Обычное состояние None
        """
        spider = self._get_spider(spider)

        if self.spiders[spider]:
            logger.info(
                f"Паук {self._get_spider_name(spider)} уже запущен. Необходимо остановить его перед запуском."
            )
            await self.alert(
                f"Паук {self._get_spider_name(spider)} уже запущен. Необходимо остановить его перед запуском."
            )
            return SpiderStatus(
                name=self._get_spider_name(spider),
                status=SpiderStatusEnum.NOT_RUNNING.value,
                message=f"Паук {self._get_spider_name(spider)} уже запущен. Необходимо остановить его перед запуском.",
            )

        try:
            await self._alert(
                f"Паук {self._get_spider_name(spider)}, начал свою работу.", "info"
            )
            self.spiders[spider] = asyncio.create_task(
                spider.run(start_page=start_page)
            )
            await self.spiders[spider]

        except (KeyboardInterrupt, asyncio.CancelledError):
            if task := self.spiders[spider]:
                if not task.done():
                    task.cancel()

            logger.warning(
                f"Паук {self._get_spider_name(spider)}, был остановлен пользователем."
            )
            await self._alert(
                f"Паук {self._get_spider_name(spider)}, был остановлен пользователем.",
                "warning",
            )
            return SpiderStatus(
                name=self._get_spider_name(spider),
                status=SpiderStatusEnum.CANCELLED.value,
                message=f"Паук {self._get_spider_name(spider)}, был остановлен пользователем.",
            )

        finally:
            logger.success(
                f"Паук {self._get_spider_name(spider)}, закончил свою работу."
            )
            self.spiders[spider] = None
            await self._alert(
                f"Паук {self._get_spider_name(spider)}, закончил свою работу.",
                "success",
            )

    async def stop_spider(self, spider: str | BaseSpider | type[BaseSpider]) -> None:
        """Остановить работу паука

        Args:
            spider (str | BaseSpider): Паук, либо название паука.
        """
        spider = self._get_spider(spider)

        if not self.spiders[spider]:
            logger.info(
                f"Паук {self._get_spider_name(spider)} не запущен. Необходимо запустить его перед остановкой."
            )
            await self._alert(
                f"Паук {self._get_spider_name(spider)} не запущен. Необходимо запустить его перед остановкой.",
                "warning",
            )
            return

        try:
            if task := self.spiders[spider]:
                if not task.done():
                    task.cancel()

                    logger.info(
                        f"Паук {self._get_spider_name(spider)}, был остановлен."
                    )
                    await self._alert(
                        f"Паук {self._get_spider_name(spider)}, был остановлен.",
                        "warning",
                    )
                else:
                    logger.info(
                        f"Паук {self._get_spider_name(spider)}, уже остановлен."
                    )
                    await self._alert(
                        f"Паук {self._get_spider_name(spider)}, уже остановлен.",
                        "warning",
                    )

            else:
                logger.warning(f"Паук {self._get_spider_name(spider)} не запущен.")
                await self._alert(
                    f"Паук {self._get_spider_name(spider)} не запущен.", "warning"
                )
        finally:
            self.spiders[spider] = None

    def _get_spider(self, spider: str | BaseSpider | type[BaseSpider]) -> BaseSpider:
        """Получает паука по название, либо самого паука.

        Args:
            spider (str | BaseSpider): Паук, либо его название

        Raises:
            ValueError: Если паук не найден
            TypeError: Если передан не поддерживаемый тип данных

        Returns:
            BaseSpider: Паук
        """
        if isinstance(spider, BaseSpider):
            return spider
        elif isinstance(spider, str):
            for _spider in self.spiders:
                if self._get_spider_name(_spider) == spider:
                    return _spider
            else:
                logger.error(f"Паук '{spider}' не существует")
                raise KeyError(f"Паук '{spider}' не существует")
        if issubclass(spider, BaseSpider):
            for _spider in self.spiders:
                if type(_spider) is spider:
                    return _spider
            else:
                logger.error(f"Паук '{spider}' не существует")
                raise KeyError(f"Паук '{spider}' не существует")
        else:
            raise TypeError(
                f"Паук должен быть либо BaseSpider, либо str, а не {type(spider)}"
            )

    def _get_spider_name(self, spider: BaseSpider) -> str:
        return spider.__class__.__name__

    async def _alert(self, message: str, level: LEVEL):
        """
        Вспомогательная функция что-бы делать оповещении.
        При отсутствии менеджера alert не будет выброшен

        Args:
            message (str): Сообщение
            level (LEVEL): Уровень сообщение
        """
        if self.alert:
            await self.alert.alert(message=message, level=level)
        else:
            logger.debug("Менеджер сообщение не передан.")

    @property
    def all_work(self) -> bool:
        return any(self.spiders.values())
