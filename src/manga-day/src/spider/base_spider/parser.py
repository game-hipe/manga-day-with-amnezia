from loguru import logger

from ...core.abstract.parser import BaseMangaParser, BasePageParser
from ...core.entities.schemas import MangaSchema, BaseManga


class GlobalMangaParser(BaseMangaParser):
    TAGS = {}

    def _parse_html(self, soup):
        title = soup.select_one("div#info h1")
        poster = soup.select_one("div#cover img")
        url = soup.select_one('link[rel="canonical"]')

        _tags = soup.select("section#tags div.tag-container")
        tags = {}

        for tag in _tags:
            if tag.next_element is None:
                continue
            tag_name = tag.next_element.get_text(strip=True).lower()

            if tag_name in self.TAGS:
                if self.TAGS[tag_name] == "genres":
                    tags[self.TAGS[tag_name]] = list(
                        set(t.get_text(strip=True) for t in tag.select("a.tag"))
                    )

                else:
                    tags[self.TAGS[tag_name]] = (
                        tag.select_one("a.tag").get_text(strip=True)
                        if tag.select_one("a.tag")
                        else None
                    )

        gallery = [
            self.urljoin(img.get("data-src"))
            for img in soup.select("div#thumbnail-container img")
            if img.get("data-src")
        ]

        logger.debug(f"Название: {title}")
        logger.debug(f"Теги: {poster}")
        logger.debug(f"URL: {url}")

        if all([title, poster, url]):
            title = title.get_text(strip=True)
            poster = self.urljoin(poster.get("data-src"))
            url = url.get("href")
        else:
            raise ValueError(
                "Не удалось извлечь данные из HTML. Пожалуйста, проверьте исходный код страницы."
            )

        if all([title, poster, url]):
            logger.debug(f"Теги: {tags}")
            return MangaSchema(
                title=title, poster=poster, url=url, **tags, gallery=gallery
            )

        raise ValueError(
            "Не удалось извлечь данные из HTML. Пожалуйста, проверьте исходный код страницы."
        )

    def _parse_json(self, data):
        raise AttributeError(
            "Этот парсер не поддерживает данные в формате JSON. Пожалуйста, используйте HTML-анализатор."
        )


class GlobalPageParser(BasePageParser):
    SELECTOR = ""

    def _parse_html(self, soup):
        exc = 0
        total = 0
        items: list[BaseManga] = []

        for item in soup.select(self.SELECTOR):
            total += 1

            title = item.get_text(strip=True)
            poster = item.select_one("img")
            url = item.select_one("a")

            if all([title, poster, url]):
                poster = self.urljoin(poster.get("data-src"))
                url = self.urljoin(url.get("href"))

            if all([title, poster, url]):
                items.append(BaseManga(title=title, poster=poster, url=url))
            else:
                exc += 1
                logger.warning("Не удалось получить обязательный атрибут")

        logger.debug(f"Удачно удалось получить обьектов {total - exc} из {total}")
        return items

    def _parse_json(self, data):
        raise AttributeError(
            "Этот парсер не поддерживает данные в формате JSON. Пожалуйста, используйте HTML-анализатор."
        )
