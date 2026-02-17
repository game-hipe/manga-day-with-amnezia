from ..base_spider.parser import GlobalMangaParser, GlobalPageParser


class MangaParser(GlobalMangaParser):
    TAGS = {"теги": "genres", "автор": "author", "язык": "language"}


class PageParser(GlobalPageParser):
    SELECTOR = "div#dle-content div.gallery"
