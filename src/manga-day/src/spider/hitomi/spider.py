from bs4 import BeautifulSoup
from loguru import logger
from pydantic import HttpUrl

from ..base_spider.spider import BaseMangaSpider
from .parser import HitomiMangaParser, HitomiPageParser


class HitomiSpider(BaseMangaSpider):
    HAS_CLOUDFARE = True

    BASE_URL = "https://hitomi.si"
    CUSTOM_COOKIES = {
        "read": "1",
    }

    PAGE_URL = "/latest?page={page}"
    """URL - для того что-бы получить максимальное число страниц"""

    MANGA = "/spa/manga/{id}/read"
    """URL - для получение галлереи"""

    PAGE_PARSER = HitomiPageParser
    MANGA_PARSER = HitomiMangaParser

    @property
    async def total_pages(self) -> int:
        if self._max_page_fetched:
            return self._total_pages

        response = await self.http.get(
            self.urljoin(
                self.PAGE_URL.format(page=99999)
            ),  # Число 99999 так-как при огромном количестве страниц сайт по просту возращает последнюю страницу
            "read",
            cookies=self.CUSTOM_COOKIES,
        )

        if response is None:
            logger.error(
                f"Не удалось получить начальную страницу для определения пагинации: {self.BASE_URL}"
            )
            self._total_pages = 1
            self._max_page_fetched = True
            return self._total_pages
        else:
            logger.debug(
                f"Получена начальная страница для определения пагинации: {self.BASE_URL}"
            )
            soup = BeautifulSoup(response, self.features)
            page_links = [
                x
                for x in soup.select("div.pagination a")
                if x.get_text(strip=True).isdigit()
            ]
            try:
                self._total_pages = max(
                    int(page.get_text(strip=True))
                    for page in page_links
                    if page.get_text(strip=True).isdigit()
                )
            except ValueError:
                logger.warning(
                    "Не удалось определить максимальную страницу. Установлено: 1"
                )
                self._total_pages = 1
            self._max_page_fetched = True
            logger.debug(
                f"Определено максимальное количество страниц: {self._total_pages}"
            )

            return self._total_pages or 1

    async def get(self, url: str, **kwargs):
        parser = HitomiMangaParser(self.BASE_URL, self.features)

        markup = await self.http.get(url, "read")
        if markup is None:
            logger.error(f"Не удалось получить страницу: {url}")
            return

        base_manga = parser.parse(markup, features=self.features, situation="html")

        id = url.split("/")[-1].replace("si", "")
        gallery = await self.http.get(self.urljoin(self.MANGA.format(id=id)), "json")
        if gallery is None:
            logger.error(f"Не удалось получить галлерею: {url}")
            return

        base_manga.gallery.extend(
            [HttpUrl(x) for x in parser.parse(gallery, situation="json")]
        )

        return base_manga
