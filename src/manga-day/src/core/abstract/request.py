import asyncio
import random
from typing import TypedDict, TypeVar, Generic, Unpack

from cachetools import TTLCache
from loguru import logger

from ..entities.schemas import ProxySchema


_T = TypeVar("_T")


class ProxyStatus(TypedDict):
    status: bool
    """Рабочий ли прокси"""

    total: int
    """Общее количество неудачных запросов"""


class RequestItem(TypedDict):
    """Аргументы для запросов"""

    max_concurrents: int | None = (None,)
    """Максимальное количество запросов одновременно."""

    max_retries: int | None = (None,)
    """Максимальное количество попыток."""

    sleep_time: int | None = (None,)
    """Время сна после запроса."""

    use_random: bool | None = (None,)
    """Использовать ли рандом во время ожидания."""

    proxy: list[ProxySchema] | None = (None,)
    """Прокси"""

    maxsize: int | None = (None,)
    """Максимальный размер кэша."""

    ttl: float | None = None
    """Время жизни кэша."""

    max_chance: int | None = None
    """Максимальное количество шансов для прокси"""

    ban_proxy: bool | None = None
    """Банить ли прокси, если он не отвечает"""


class BaseRequestManager(Generic[_T]):
    """Менеджер для запросов."""

    SLEEP_TIME: int = 2
    """Базовое время сна, после запроса."""

    USE_RANDOM: int = True
    """Базовое значение, использование рандома при ожидании"""

    MAX_CONCURRENTS: int = 5
    """Базовое значение, количество запросов одновременно"""

    MAX_RETRIES: int = 5
    """Базовое значение, максимальное количество попыток."""

    MAX_CHANCE: int = 3
    """Базовое значение, максимального количество шансов для прокси, по истечению которых прокси буден указан как не рабочий"""

    MAXSIZE: int = 128
    """Базовое значение, максимального размера кэша."""

    TTL: float = 300
    """Базовое значение, время жизни кэша."""

    BASE_PROXY: type[ProxySchema] = ProxySchema
    """Базовое значение, класса прокси"""

    BAN_PROXY: bool = False
    """Базовое значение, если прокси не отвечает"""

    def __init__(self, session: _T, **kw: Unpack[RequestItem]):
        """Ицилизация RequestManager

        Args:
            session (_T): Сессия для работы с запросами.
            max_concurrents (int, None, optional): Максимальное количество запросов.
            max_retries (int, None, optional): Максимальное количество попыток.
            sleep_time (int, None, optional): Время сна после запроса. Обычное значени SLEEP_TIME.
            use_random (bool, optional): Использовать ли рандом во время ожидания. Обычное значени USE_RANDOM.
            proxy (list[ProxySchema], optional): Прокси. Обычное значение [].
        """
        self.session = session
        self.max_concurrents = kw.get("max_concurrents") or self.MAX_CONCURRENTS
        self.max_retries = kw.get("max_retries") or self.MAX_RETRIES
        self.sleep_time = kw.get("sleep_time") or self.SLEEP_TIME
        self.use_random = kw.get("use_random") or self.USE_RANDOM
        self.max_chance = kw.get("max_chance") or self.MAX_CHANCE
        self._ban_proxy = kw.get("ban_proxy") or self.BAN_PROXY

        self.semaphore = asyncio.Semaphore(self.max_concurrents)
        self.proxy: dict[ProxySchema, ProxyStatus] = {
            self.BASE_PROXY.model_validate(x.model_dump()): {"status": True, "total": 0}
            for x in kw.get("proxy") or []
        }

        self.cache = TTLCache(
            maxsize=kw.get("maxsize") or self.MAXSIZE, ttl=kw.get("ttl") or self.TTL
        )

    async def sleep(self, time: float | None = None):
        await asyncio.sleep(
            (time or self.sleep_time) * (random.uniform(0, 1) if self.use_random else 1)
        )

    def get_proxy(self) -> ProxySchema | None:
        if not self.proxy:
            return None

        work_proxy = list(filter(lambda x: self.proxy[x]["status"], self.proxy))
        if not work_proxy:
            logger.debug("Больше нет рабочих прокси")
            return None

        proxy = random.choice(work_proxy)
        return proxy

    def wrong_response(self, proxy: ProxySchema):
        logger.debug(f"Ошибка у прокси (proxy={proxy.proxy})")
        self.proxy[proxy]["total"] += 1
        if self.proxy[proxy]["total"] >= self.max_chance:
            self.ban_proxy(proxy)

    def ban_proxy(self, proxy: ProxySchema):
        if self._ban_proxy:
            self.proxy[proxy]["status"] = False
