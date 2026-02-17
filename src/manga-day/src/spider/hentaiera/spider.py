import json
import re

from typing import Literal

import aiohttp

from loguru import logger
from bs4 import BeautifulSoup
from pydantic import HttpUrl

from ..base_spider.spider import BaseMangaSpider
from .parser import MangaHentaiEraParser, PageHentaiEraParser


class HentaiEraSpider(BaseMangaSpider):
    MAX_PAGE_SELECTOR = "ul.pagination a.page-link"
    SITE_TIMEOUT = 10
    BASE_URL = "https://hentaiera.com"
    READ_URL = "/view/{id}/1/"
    PAGE_URL = "/?page={page}"
    MANGA_PARSER = MangaHentaiEraParser
    PAGE_PARSER = PageHentaiEraParser

    GET_GALLERY_PATTERN = r"parseJSON\('(.*?)'\);"

    async def get(self, url: str, **kw):
        kw["timeout"] = kw.get(
            "timeout",
            aiohttp.ClientTimeout(
                total=self.SITE_TIMEOUT  # NOTE: Обусовлено количество времени тем-что сайт может "Зависнуть", и из-за этого требуется сократить timeout.
            ),
        )

        manga = await super().get(url, **kw)

        if manga is None:
            return

        id = self._extract_id(url)
        gallery = await self._get_gallery(id)

        if gallery is None:
            logger.error(f"Не удалось получить галлерею для {url}")
            return
        else:
            manga.gallery = [HttpUrl(x) for x in gallery]
            return manga

    async def _get_gallery(self, id: int) -> list[str] | None:
        response = await self.http.get(
            self.urljoin(self.READ_URL.format(id=id)), "read"
        )

        if response is None:
            logger.error("Не удалось получить галлерею")
            return

        soup = BeautifulSoup(response, self.features)
        return self._extract_gallery(soup)

    def _extract_gallery(self, soup: BeautifulSoup) -> list[str]:
        images = []
        gallery_info = None
        for x in soup.select('script[type="text/javascript"]'):
            script = x.get_text(strip=True)
            match = re.search(self.GET_GALLERY_PATTERN, script)
            if match:
                gallery_info = json.loads(match.group(1))

        if not gallery_info:
            raise ValueError("Не удалось получить параметры галлереии")

        pages = soup.select_one("#pages")
        image_dir = soup.select_one("#image_dir")
        gallery_id = soup.select_one("#gallery_id")
        u_id = soup.select_one("#u_id")

        if not all([pages, image_dir, gallery_id, u_id]):
            raise ValueError("Не удалось получить один из элементов")

        pages = pages.get("value")
        image_dir = image_dir.get("value")
        gallery_id = gallery_id.get("value")
        u_id = u_id.get("value")

        for page in range(1, int(pages) + 1):
            server = self.get_random_server(u_id)
            suffix = self._gallery_thumb(page, gallery_info)
            images.append(self._build_url(server, image_dir, gallery_id, page, suffix))

        return images

    @staticmethod
    def _extract_id(url: str) -> int:
        return int("".join(x for x in url.split("/") if x.isdigit()))

    @staticmethod
    def _build_url(
        server: str, image_dir: str, gallery_id: int, page: int, suffix: str
    ) -> str:
        return f"https://{server}/{image_dir}/{gallery_id}/{page}.{suffix}"

    @staticmethod
    def _gallery_thumb(
        page: int | str, gallery_info: dict[str, str]
    ) -> Literal["jpg", "png", "bmp", "gif", "webp"]:
        """Получает формат фотографии

        Args:
            page (int | str): страница
            gallery_info (dict[str, str]): Информация о галлереи

        Returns:
            Literal["jpg", "png", "bmp", "gif", "webp"]: Формат фотографии
        """
        info = gallery_info[str(page)]
        img_type, width, heigh = info.split(",")
        if img_type == "j":
            return "jpg"
        if img_type == "p":
            return "png"
        if img_type == "b":
            return "bmp"
        if img_type == "g":
            return "gif"
        if img_type == "w":
            return "webp"

    @staticmethod
    def get_random_server(
        u_id: int,
    ) -> Literal[
        "m1.hentaiera.com",
        "m2.hentaiera.com",
        "m3.hentaiera.com",
        "m4.hentaiera.com",
        "m5.hentaiera.com",
        "m6.hentaiera.com",
        "m7.hentaiera.com",
        "m8.hentaiera.com",
        "m9.hentaiera.com",
        "m10.hentaiera.com",
    ]:
        """
        Определяет сервер на основе ID пользователя

        Args:
            u_id: ID пользователя (целое число)

        Returns:
            str: адрес сервера
        """
        u_id = int(u_id)
        if 0 < u_id <= 274825:
            return "m1.hentaiera.com"
        elif 274825 < u_id <= 403818:
            return "m2.hentaiera.com"
        elif 403818 < u_id <= 527143:
            return "m3.hentaiera.com"
        elif 527143 < u_id <= 632481:
            return "m4.hentaiera.com"
        elif 632481 < u_id <= 815858:
            return "m5.hentaiera.com"
        elif 815858 < u_id <= 969848:
            return "m6.hentaiera.com"
        elif 969848 < u_id <= 1120799:
            return "m7.hentaiera.com"
        elif 1120799 < u_id <= 1257317:
            return "m8.hentaiera.com"
        elif 1257317 < u_id <= 1433861:
            return "m9.hentaiera.com"
        else:
            return "m10.hentaiera.com"
