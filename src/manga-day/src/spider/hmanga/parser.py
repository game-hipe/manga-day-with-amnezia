from ..base_spider.parser import GlobalMangaParser, GlobalPageParser


class MangaParser(GlobalMangaParser):
    TAGS = {"contents": "genres", "artist": "author", "language": "language"}


class PageParser(GlobalPageParser):
    SELECTOR = 'div[class="container index-container"] div.gallery'
