"""Загрузка пауков."""

import importlib

from typing import Unpack, overload

import aiohttp

from loguru import logger

from ...abstract.spider import BaseSpider
from ...abstract.request import BaseRequestManager, RequestItem
from ..manga import MangaManager


ERROR_ALL_NOT_FOUND = "Не удалось загрузить список доступных парсеров. Пожалуйста, проверьте наличие файла __all__ в модуле spider."
ERROR_SPIDER_NOT_FOUND = "Паук {spider} не найден. Пожалуйста, проверьте наличие файла __all__ в модуле spider."
WARNING_SPIDER_CLOUDFARE = (
    "Парсер {spider} использует CloudFare. Парсер будет пропущен при инцилизации"
)
WARNING_SPIDER_BANNED = (
    "Парсер {spider} указан как заблокированный. Парсер будет пропущен при инцилизации"
)


@overload
def load_spiders(
    session: BaseRequestManager,
    banned_spider: list[type[BaseSpider]] = [],
    manager: MangaManager | None = None,
    features: str | None = None,
    batch: int | None = None,
) -> list[BaseSpider]:
    """Динамически загружает пауков, из директории, "spider" которые находятся внутри __all__

    Args:
        session (BaseRequestManager): Сессия для запросов.
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
def load_spiders(
    session: aiohttp.ClientSession,
    banned_spider: list[type[BaseSpider]] = [],
    manager: MangaManager | None = None,
    features: str | None = None,
    batch: int | None = None,
    **kwargs: Unpack[RequestItem],
) -> list[BaseSpider]:
    """Динамически загружает пауков, из директории, "spider" которые находятся внутри __all__

    Args:
        session (aiohttp.ClientSession): Сессия aiohttp для запросов.
        banned_spider (list[type[BaseSpider]]): Пауки которых не нужно загружать. Обычное состояние []
        manager (MangaManager | None, optional): Менеджер манги. Обычное состояние None
        features (str | None, optional): Движок для парсинга. Обычное состояние None
        batch (int | None, optional): Размер пачки для парсинга. Обычное состояние None

    Returns:
        list[BaseSpider]: Инцилизированные пауки.

    Warning:
        Если manager не будет указан функция run, перестанет работать.
    """


def load_spiders(
    session: aiohttp.ClientSession | BaseRequestManager,
    banned_spider: list[type[BaseSpider]] = [],
    manager: MangaManager | None = None,
    features: str | None = None,
    batch: int | None = None,
    **kwargs,
) -> list[BaseSpider]:
    """Динамически загружает пауков, из директории, "spider" которые находятся внутри __all__

    Args:
        session (aiohttp.ClientSession | BaseRequestManager): Сессия aiohttp, либо базовый менеджер запросов.
        banned_spider (list[type[BaseSpider]]): Пауки которых не нужно загружать. Обычное состояние []
        manager (MangaManager | None, optional): Менеджер манги. Обычное состояние None
        features (str | None, optional): Движок для парсинга. Обычное состояние None
        batch (int | None, optional): Размер пачки для парсинга. Обычное состояние None

    Returns:
        list[BaseSpider]: Инцилизированные пауки.

    Warning:
        Если manager не будет указан функция run, перестанет работать.
    """
    if manager is None:
        logger.warning("Менеджер не указан, функция None работать перестаёт работать.")

    spiders: list[BaseSpider] = []
    spider_module = importlib.import_module("....spider", package=__package__)

    if not hasattr(spider_module, "__all__"):
        logger.error(ERROR_ALL_NOT_FOUND)
        raise ImportError(ERROR_ALL_NOT_FOUND)

    for spider_name in spider_module.__all__:
        if not hasattr(spider_module, spider_name):
            logger.error(ERROR_SPIDER_NOT_FOUND.format(spider=spider_name))
            continue

        spider_factory: type[BaseSpider] = getattr(spider_module, spider_name)

        if hasattr(spider_factory, "HAS_CLOUDFARE") and getattr(
            spider_factory, "HAS_CLOUDFARE"
        ):
            logger.warning(WARNING_SPIDER_CLOUDFARE.format(spider=spider_name))
            continue

        if spider_factory in banned_spider:
            logger.warning(WARNING_SPIDER_BANNED.format(spider=spider_name))
            continue

        spider = spider_factory(
            session=session, manager=manager, features=features, batch=batch, **kwargs
        )

        spiders.append(spider)

    if not spiders:
        raise ValueError(
            "Не удалось загрузить ни одного парсера. Пожалуйста, проверьте наличие классов в модуле spider."
        )

    logger.debug(
        f"Загружено {len(spiders)} парсеров: {', '.join(spider.__class__.__name__ for spider in spiders)}"
    )
    return spiders
