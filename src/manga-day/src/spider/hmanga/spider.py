from ..base_spider.spider import BaseMangaSpider
from .parser import MangaParser, PageParser


class HmangaSpider(BaseMangaSpider):
    BASE_URL = "https://hmanga.my/"
    MANGA_PARSER = MangaParser
    PAGE_PARSER = PageParser
