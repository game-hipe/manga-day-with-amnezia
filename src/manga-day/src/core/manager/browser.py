from typing import AsyncGenerator
from contextlib import asynccontextmanager

from patchright.async_api import Browser, Page
from loguru import logger

from ..abstract.request import BaseRequestManager


__all__ = ["RequestBrowserManager"]


class RequestBrowserManager(BaseRequestManager[Browser]):
    @asynccontextmanager
    async def get(self, url: str) -> AsyncGenerator[Page, None]:
        async with self.semaphore:
            context = None
            page = None
            for try_indx in range(self.max_retries):
                try:
                    context = await self.session.new_context()
                    page = await context.new_page()

                    response = await page.goto(url)

                    if response is None:
                        logger.warning(
                            f"Не удалось получить данные (url={url}, try-indx={try_indx})"
                        )

                    if response.status == 404:
                        logger.warning("Страница не найдена, 404")

                    elif response.status == 403:
                        logger.warning("Страница заблокировано")

                    elif 500 <= response.status < 600:
                        logger.warning("Ошибка сервера, новая попытка...")
                        self.sleep()
                        continue

                    yield page
                    break

                finally:
                    if page is not None:
                        await page.close()

                    if context is not None:
                        await context.close()
