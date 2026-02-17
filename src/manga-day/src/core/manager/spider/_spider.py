"""Менеджер пауков."""

import asyncio

from typing import overload, Unpack

import aiohttp

from ._load import load_spiders
from ._starter import SpiderStarter
from ._status import SpiderStatus, SpiderStatusEnum
from ..manga import MangaManager
from ..alert import AlertManager
from ...abstract.request import BaseRequestManager, RequestItem
from ...abstract.spider import BaseSpider


class SpiderManager:
    @overload
    def __init__(
        self,
        session: BaseRequestManager,
        alert: AlertManager | None = None,
        banned_spider: list[type[BaseSpider]] = [],
        manager: MangaManager | None = None,
        features: str | None = None,
        batch: int | None = None,
    ) -> None:
        """Менеджер пауков, через него можно запустить парсинг со всех пауков, так-же получить статус каждого.

        Args:
            session (BaseRequestManager): Сессия для запросов.
            alert: (AlertManager | None, optional): Менеджер оповещений. Обычное состояние None
            banned_spider (list[type[BaseSpider]]): Пауки которых не нужно загружать. Обычное состояние []
            manager (MangaManager | None, optional): Менеджер манги. Обычное состояние None
            features (str | None, optional): Движок для парсинга. Обычное состояние None
            batch (int | None, optional): Размер пачки для парсинга. Обычное состояние None

        Returns:
            list[BaseSpider]: Инцилизированные пауки.

        Warning:
            Если manager не будет указан функция run, перестанет работать.
        """

    @overload
    def __init__(
        self,
        session: aiohttp.ClientSession,
        alert: AlertManager | None = None,
        banned_spider: list[type[BaseSpider]] = [],
        manager: MangaManager | None = None,
        features: str | None = None,
        batch: int | None = None,
        **kwargs: Unpack[RequestItem],
    ) -> None:
        """Менеджер пауков, через него можно запустить парсинг со всех пауков, так-же получить статус каждого.

        Args:
            session (aiohttp.ClientSession): Сессия aiohttp для запросов.
            alert: (AlertManager | None, optional): Менеджер оповещений. Обычное состояние None
            banned_spider (list[type[BaseSpider]]): Пауки которых не нужно загружать. Обычное состояние []
            manager (MangaManager | None, optional): Менеджер манги. Обычное состояние None
            features (str | None, optional): Движок для парсинга. Обычное состояние None
            batch (int | None, optional): Размер пачки для парсинга. Обычное состояние None

        Returns:
            list[BaseSpider]: Инцилизированные пауки.

        Warning:
            Если manager не будет указан функция run, перестанет работать.
        """

    def __init__(
        self,
        session: aiohttp.ClientSession | BaseRequestManager,
        alert: AlertManager | None = None,
        banned_spider: list[type[BaseSpider]] = [],
        manager: MangaManager | None = None,
        features: str | None = None,
        batch: int | None = None,
        **kwargs,
    ) -> None:
        """Менеджер пауков, через него можно запустить парсинг со всех пауков, так-же получить статус каждого.

        Args:
            session (aiohttp.ClientSession | BaseRequestManager): Сессия aiohttp, либо базовый менеджер запросов.
            alert: (AlertManager | None, optional): Менеджер оповещений. Обычное состояние None
            banned_spider (list[type[BaseSpider]]): Пауки которых не нужно загружать. Обычное состояние []
            manager (MangaManager | None, optional): Менеджер манги. Обычное состояние None
            features (str | None, optional): Движок для парсинга. Обычное состояние None
            batch (int | None, optional): Размер пачки для парсинга. Обычное состояние None

        Returns:
            list[BaseSpider]: Инцилизированные пауки.

        Warning:
            Если manager не будет указан функция start_full_parsing, перестанет работать.
        """
        self.spiders = load_spiders(
            session=session,
            banned_spider=banned_spider,
            manager=manager,
            features=features,
            batch=batch,
            **kwargs,
        )

        self.alert = alert
        self._manager = bool(manager)
        self._starter = SpiderStarter(self.spiders, self.alert)

    async def start_full_parsing(self) -> None:
        """Начинает полное сканирование, сайтов.

        Raises:
            AttributeError: Если менеджер не был передан
        """
        if not self._manager:
            raise AttributeError(
                "Менеджер не был передан. Убедитесь, что менеджер передан перед запуском парсинга."
            )
        if all([x.status == SpiderStatusEnum.RUNNING for x in self.status]):
            await self.starter._alert(
                "Все пауки уже запущены, перезапуск не требуется.", "INFO"
            )
            return
        tasks = []
        for spider in self.spiders:
            tasks.append(asyncio.create_task(self._starter.start_spider(spider)))
        try:
            await asyncio.shield(asyncio.gather(*tasks, return_exceptions=True))
        finally:
            await asyncio.shield(self.stop_all_spider())

    async def stop_all_spider(self) -> None:
        """Останавливает все пауки."""
        tasks = []
        for spider in self.spiders:
            tasks.append(asyncio.create_task(self._starter.stop_spider(spider)))

        await asyncio.gather(*tasks, return_exceptions=True)

    @property
    def status(self) -> list[SpiderStatus]:
        """Возвращает статус всех пауков."""
        all_status = []
        for spider in self.starter.spiders:
            all_status.append(self.get_spider_status(spider))
        return all_status

    @property
    def starter(self) -> SpiderStarter:
        """Возращает стартер пауков

        Returns:
            SpiderStarter: старте паука.
        """
        return self._starter

    def get_spider_status(
        self, spider: BaseSpider | type[BaseSpider] | str
    ) -> SpiderStatus:
        """Получает статус паука

        Args:
            spider (BaseSpider | type[BaseSpider] | str): Сам паук

        Returns:
            SpiderStatus: Статус об пауке
        """
        spider = self.starter._get_spider(spider)
        return SpiderStatus(
            name=spider.__class__.__name__,
            status=self._convert_status(self.starter.spiders[spider]),
            message=spider.status if hasattr(spider, "status") else None,
        )

    @staticmethod
    def _convert_status(task: asyncio.Task | None) -> SpiderStatusEnum:
        """Вспомогательная функция что-бы возращать тип

        Args:
            task (asyncio.Task | None): Задачаm или None

        Returns:
            SpiderStatusEnum: Статус задачи
        """
        if task is None:
            return SpiderStatusEnum.NOT_RUNNING

        if task.cancelled():
            return SpiderStatusEnum.CANCELLED

        elif task.done():
            if task.exception():
                return SpiderStatusEnum.CANCELLED

            else:
                return SpiderStatusEnum.SUCCESS
        else:
            return SpiderStatusEnum.RUNNING
