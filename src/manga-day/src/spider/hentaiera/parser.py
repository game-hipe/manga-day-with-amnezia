from bs4 import Tag, BeautifulSoup
from loguru import logger

from ...core.entities.schemas import MangaSchema, BaseManga
from ...core.abstract.parser import BaseMangaParser, BasePageParser


class MangaHentaiEraParser(BaseMangaParser):
    MANGA = "/gallery/{id}/"
    GENRES = {"tags": "genres", "artists": "author", "languages": "language"}

    def _parse_html(self, soup):
        title = soup.select_one("h1")
        poster = soup.select_one("div.left_cover img")
        url = self._extract_url(soup.select_one("input#gallery_id"))

        tags = self._extract_tags(soup)

        if not all([title, poster, url]):
            raise ValueError(
                "Не удалось извлечь данные из HTML. Пожалуйста, проверьте исходный код страницы."
            )

        return MangaSchema(
            title=title.get_text(strip=True),
            poster=poster.get("data-src"),
            url=url,
            **tags,
        )

    def _parse_json(self, data):
        raise NotImplementedError(
            "Данный паук не поддерживает JSON, пожалуйста используйте HTML"
        )

    def _extract_tags(self, soup: BeautifulSoup):
        tags = {}
        for tag in soup.select("ul.galleries_info li"):
            tags |= self._get_tag(tag)

        return tags

    def _extract_url(self, tag: Tag | None) -> str:
        if tag is None:
            raise ValueError("Не найден тэг с ID")

        id = tag.get("value")
        if id is None:
            raise ValueError("Не удалось достать ID")

        manag_url = self.MANGA.format(id=id)
        return self.urljoin(manag_url)

    def _get_tag(self, tag: Tag) -> dict[str, str | list[str]]:
        tag_name = tag.select_one(".tags_text")
        if tag_name is None:
            return {}

        text = tag_name.get_text(strip=True)
        if text.lower() not in self.GENRES:
            return {}

        tag_name = self.GENRES[text.lower()]
        if tag_name == "genres":
            return {
                tag_name: [x.get_text(strip=True) for x in tag.select(".item_name")]
            }
        else:
            return {
                tag_name: tag.select_one(".item_name").get_text(strip=True)
                if tag.select_one(".item_name")
                else None
            }


class PageHentaiEraParser(BasePageParser):
    def _parse_html(self, soup):
        mangas = []
        logger.debug("Парсинг данных (HTML)")
        for thumb in soup.select("div.row.galleries div.thumb"):
            title = thumb.select_one("h2")
            poster = thumb.select_one("img")
            url = thumb.select_one("h2.gallery_title a")

            if all([title, poster, url]):
                title = title.get_text(strip=True)
                poster = self.urljoin(poster.get("data-src"))
                url = self.urljoin(url.get("href"))
                mangas.append(BaseManga(title=title, poster=poster, url=url))

            else:
                logger.warning(
                    f"Не удалось получить обязательный атрибут (title={title}, poster={poster}, url={url})"
                )
                continue

        return mangas

    def _parse_json(self, data):
        raise NotImplementedError(
            "Данный паук не поддерживает JSON, пожалуйста используйте HTML-анализатор."
        )
