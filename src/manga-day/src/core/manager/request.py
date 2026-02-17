from typing import Unpack, Literal, TypeAlias, overload

from fake_headers import Headers
from aiohttp import ClientSession
from aiohttp import ClientResponseError, ServerDisconnectedError
from aiohttp.client import _RequestOptions
from aiohttp import ClientOSError
from loguru import logger

from ..abstract.request import BaseRequestManager
from ..entities.schemas import AiohttpProxy

ReturnType: TypeAlias = Literal["text", "read"]


class RequestManager(BaseRequestManager[ClientSession]):
    BASE_PROXY = AiohttpProxy

    def __init__(self, session, **kw):
        super().__init__(session, **kw)
        self.headers = Headers()

    @overload
    async def request(
        self,
        method: str,
        url: str,
        type: Literal["text"],
        **kwargs: Unpack[_RequestOptions],
    ) -> str | None:
        """Функция, для запросов с системой повторных попыток.

        Args:
            method (str): Метод, для получение страницы (GET, POST, и т п.)
            url (str): Путь к интернет странице
            type (Literal["text"]): Возращает текст страницы

        Returns:
            str | None: Возращает текст страницы
        """

    @overload
    async def request(
        self,
        method: str,
        url: str,
        type: Literal["read"],
        **kwargs: Unpack[_RequestOptions],
    ) -> bytes | None:
        """Функция, для запросов с системой повторных попыток.

        Attributes:
            method (str): Метод, для получение страницы (GET, POST, и т п.)
            url (str): Путь к интернет странице
            type (Literal["read"]): Возращает бинарные данные

        Returns:
            bytes | None: Возращает данные с страницы
        """

    @overload
    async def get(
        self, url: str, type: Literal["text"], **kwargs: Unpack[_RequestOptions]
    ) -> str | None:
        """Функция, для запросов с системой повторных попыток. имеет готовый атрибут GET

        Attributes:
            url (str): Путь к интернет странице
            type (Literal["text"]): Возращает текст страницы

        Returns:
            str | None: Возращает текст страницы
        """

    @overload
    async def get(
        self, url: str, type: Literal["read"], **kwargs: Unpack[_RequestOptions]
    ) -> bytes | None:
        """Функция, для запросов с системой повторных попыток. имеет готовый атрибут GET

        Attributes:
            url (str): Путь к интернет странице
            type (Literal["read"]): Возращает бинарные данные

        Returns:
            bytes | None: Возращает данные с страницы
        """

    @overload
    async def post(
        self, url: str, type: Literal["text"], **kwargs: Unpack[_RequestOptions]
    ) -> str | None:
        """Функция, для запросов с системой повторных попыток. имеет готовый атрибут POST

        Attributes:
            url (str): Путь к интернет странице
            type (Literal["text"]): Возращает текст страницы

        Returns:
            str | None: Возращает текст страницы
        """

    @overload
    async def post(
        self, url: str, type: Literal["read"], **kwargs: Unpack[_RequestOptions]
    ) -> bytes | None:
        """Функция, для запросов с системой повторных попыток. имеет готовый атрибут POST

        Attributes:
            url (str): Путь к интернет странице
            type (Literal["read"]): Возращает бинарные данные

        Returns:
            bytes | None: Возращает данные с страницы
        """

    async def request(
        self, method: str, url: str, type: ReturnType, **kwargs: Unpack[_RequestOptions]
    ) -> str | bytes | None:
        """Функция, для запросов с системой повторных попыток.

        Attributes:
            method (str): Метод, для получение страницы (GET, POST, и т п.)
            url (str): Путь к интернет странице
            type (str): тип возращаемых данных

        Returns:
            str | bytes | None: Возращает данные с страницы
        """
        if f"{method}{url}" in self.cache:
            logger.info(f"Используется кэш (url={url}, method={method})")
            return self.cache[f"{method}{url}"]

        async with self.semaphore:
            logger.info(f"Попытка получить страницу (url={url}, method={method})")
            for _ in range(self.max_retries):
                proxy = self.get_proxy()
                templates = {}
                try:
                    if proxy:
                        templates = kwargs | proxy.auth()

                    templates["headers"] = kwargs.get(
                        "headers", self.headers.generate()
                    )

                    async with self.session.request(
                        method, url, **templates
                    ) as response:
                        response.raise_for_status()
                        result = await getattr(response, type)()
                        logger.info(
                            f"Удалось получить страницу (url={url}, method={method}, result_len={len(result)})"
                        )
                        self.cache[f"{method}{url}"] = result
                        return result

                except ClientResponseError as error:
                    if error.status == 404:
                        logger.warning(
                            f"Страницы не существует (url={url}, method={method})"
                        )
                        return

                    elif error.status == 403:
                        logger.warning(
                            f"Страница недоступна (url={url}, method={method}, message={error.message})"
                        )
                        return

                    elif error.status == 407:
                        logger.warning(
                            f"Прокси более не доступен (proxy={proxy.proxy})"
                        )
                        if proxy:
                            self.ban_proxy(proxy)
                    logger.error(
                        f"Не удалось получить страницу (url={url}, method={method}, message={error.message}, status={error.status})"
                    )

                except ServerDisconnectedError:
                    logger.error("Сервер принудительно отключил нас от сервера.")

                # Новый обработчик для Connection reset by peer
                except ConnectionResetError as error:
                    logger.error(
                        f"Соединение было сброшено (Connection reset by peer) (url={url}, method={method}, error={error})"
                    )

                except ClientOSError as error:
                    # если ClientOSError содержит текст '[Errno 104] Connection reset by peer',
                    # логируем это отдельно
                    err_str = str(error)
                    if (
                        "[Errno 104]" in err_str
                        or "Connection reset by peer" in err_str
                    ):
                        logger.error(
                            f"Ошибка: [Errno 104] Connection reset by peer (url={url}, method={method}, error={error})"
                        )
                    else:
                        logger.error(
                            f"Ошибка сети: разрыв соединения или недоступность сервера. (error={error})"
                        )

                except TimeoutError:
                    logger.error(
                        f"Превышено время ожидание ответа, новая попытка (url={url}, method={method})"
                    )
                    if proxy:
                        self.wrong_response(proxy)

                finally:
                    await self.sleep()

            logger.error(f"Не удалось получить страницу за {self.max_retries} попыток")

    async def get(
        self, url: str, type: ReturnType, **kwargs: Unpack[_RequestOptions]
    ) -> str | bytes | None:
        return await self.request("GET", url, type=type, **kwargs)

    async def post(
        self, url: str, type: ReturnType, **kwargs: Unpack[_RequestOptions]
    ) -> str | bytes | None:
        return await self.request("POST", url, type=type, **kwargs)

    def _get_headers(self):
        return self.headers.generate()
