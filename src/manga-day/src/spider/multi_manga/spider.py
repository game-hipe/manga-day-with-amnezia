from ..base_spider.spider import BaseMangaSpider
from .parser import MangaParser, PageParser


class MultiMangaSpider(BaseMangaSpider):
    BASE_URL = "https://multi-manga.today"
    MANGA_PARSER = MangaParser
    PAGE_PARSER = PageParser
