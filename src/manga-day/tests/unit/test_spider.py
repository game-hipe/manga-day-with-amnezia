import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import pytest_asyncio
from aiohttp import ClientSession
from cachetools import TTLCache
from src.spider.hmanga import HmangaSpider
from src.spider.multi_manga import MultiMangaSpider
from src.spider.hitomi import HitomiSpider
from src.spider.hentaiera import HentaiEraSpider

CACHE = TTLCache(128, 300)


class BaseSpiderTest:
    """Базовый класс для тестирования спайдеров"""

    @pytest_asyncio.fixture
    async def session(self):
        """Асинхронная фикстура для создания сессии"""
        async with ClientSession() as session:
            yield session

    @pytest.mark.asyncio
    async def test_spider_connectivity(self, spider):
        """Тест подключения к сайту"""
        result = await spider.http.get(self.BASE_URL, "text")
        if result is None:
            pytest.skip(
                "Не удалось соединиться с сайтом, возможно стоит включить VPN либо сменить домен."
            )
        assert result is not None

    @pytest_asyncio.fixture
    async def manga_data(self, spider):
        """Фикстура для получения данных манги (кеширование запроса)"""
        if CACHE.get(self.TEST_URL) is not None:
            return CACHE[self.TEST_URL]
        else:
            result = await spider.get(self.TEST_URL)
            CACHE[self.TEST_URL] = result
            return result


class TestSpiderMultiManga(BaseSpiderTest):
    BASE_URL = "https://multi-manga.today"
    TEST_URL = "https://multi-manga.today/16126-moja-povsednevnaja-zhizn-s-sestroj-grjaznulej-kotoroj-nuzhen-tolko-seks-esli-pobedish-sestrenku-to-ja-razreshu-tebe-konchit-bez-rezinki-boku-to.html"

    TAGS = [
        "ahegao",
        "x-ray",
        "анал",
        "анилингус",
        "без трусиков",
        "большая грудь",
        "большие попки",
        "вибратор",
        "волосатые женщины",
        "глубокий минет",
        "групповой секс",
        "инцест",
        "кремпай",
        "купальники",
        "мастурбация",
        "мать",
        "мерзкий дядька",
        "минет",
        "молоко",
        "обычный секс",
        "огромная грудь",
        "оплодотворение",
        "сетакон",
        "чулки",
        "школьная форма",
        "школьный купальник",
    ]

    EXPECTED_TITLE = (
        "Моя повседневная жизнь с сестрой-грязнулей, которой нужен только секс "
        "~Если победишь сестрёнку, то я разрешу тебе кончить без резинки!~ "
        "(Boku to Gasatsu na Onee no Seiyoku Shori Seikatsu "
        "~Onee-chan ni Katetara Ninshin Kakugo de Nama Ecchi Hen~)"
    )
    EXPECTED_LANGUAGE = "Русский"
    EXPECTED_POSTER = (
        "https://multi-manga.today/uploads/posts/2026-01/medium/1767914666_01.webp"
    )
    EXPECTED_GALLERY_COUNT = 36
    EXPECTED_AUTHOR = "Jovejun"

    @pytest_asyncio.fixture
    async def spider(self, session):
        return MultiMangaSpider(session)

    @pytest.mark.asyncio
    async def test_spider_get_manga(self, manga_data):
        assert manga_data is not None

    @pytest.mark.asyncio
    async def test_spider_get_title(self, manga_data):
        assert manga_data.title == self.EXPECTED_TITLE

    @pytest.mark.asyncio
    async def test_spider_get_genres(self, manga_data):
        for tag in self.TAGS:
            assert tag in manga_data.genres

    @pytest.mark.asyncio
    async def test_spider_get_language(self, manga_data):
        assert manga_data.language == self.EXPECTED_LANGUAGE

    @pytest.mark.asyncio
    async def test_spider_get_poster(self, manga_data):
        assert str(manga_data.poster) == self.EXPECTED_POSTER

    @pytest.mark.asyncio
    async def test_spider_get_gallery(self, manga_data):
        assert len(manga_data.gallery) == self.EXPECTED_GALLERY_COUNT

    @pytest.mark.asyncio
    async def test_spider_get_author(self, manga_data):
        assert manga_data.author == self.EXPECTED_AUTHOR


class TestSpiderHmanga(BaseSpiderTest):
    BASE_URL = "https://hmanga.my"
    TEST_URL = "https://hmanga.my/14674-hagure-moguri-ogaritai-hitozuma-kateikyoushi-musuko-to-danna-ga-inai-sabishii-seikatsu-o-okutteru-naraboku-no-mama-ni-natte-chinese.html"

    TAGS = [
        "Big Ass",
        "Big Breasts",
        "Cheating",
        "MILF",
        "Nakadashi",
        "Shotacon",
        "Sole Female",
        "Sole Male",
        "Tutor",
    ]

    EXPECTED_TITLE = (
        "[Hagure Moguri] Ogaritai Hitozuma Kateikyoushi "
        "~Musuko to Danna ga Inai Sabishii Seikatsu o Okutteru Naraboku no Mama ni Natte~ "
        "[Chinese]"
    )
    EXPECTED_LANGUAGE = "chinese"
    EXPECTED_POSTER = "https://hmanga.my/uploads/posts/2026-01/medium/1767911442_1.webp"
    EXPECTED_GALLERY_COUNT = 38

    @pytest_asyncio.fixture
    async def spider(self, session):
        return HmangaSpider(session)

    @pytest.mark.asyncio
    async def test_spider_get_manga(self, manga_data):
        assert manga_data is not None

    @pytest.mark.asyncio
    async def test_spider_get_title(self, manga_data):
        assert manga_data.title == self.EXPECTED_TITLE

    @pytest.mark.asyncio
    async def test_spider_get_genres(self, manga_data):
        for tag in self.TAGS:
            assert tag in manga_data.genres

    @pytest.mark.asyncio
    async def test_spider_get_language(self, manga_data):
        assert manga_data.language == self.EXPECTED_LANGUAGE

    @pytest.mark.asyncio
    async def test_spider_get_poster(self, manga_data):
        assert str(manga_data.poster) == self.EXPECTED_POSTER

    @pytest.mark.asyncio
    async def test_spider_get_gallery(self, manga_data):
        assert len(manga_data.gallery) == self.EXPECTED_GALLERY_COUNT

    @pytest.mark.asyncio
    async def test_spider_get_author(self, manga_data):
        assert manga_data.author is None

    @pytest.mark.asyncio
    async def test_spider_run(self, spider):
        with pytest.raises(AttributeError):
            await spider.run()


class TestSpiderHitomi(BaseSpiderTest):
    BASE_URL = "https://hitomi.si"
    TEST_URL = "https://hitomi.si/mangazine/si101093"

    TAGS = [
        "milf",
        "mother",
        "sister",
        "aunt",
        "father",
    ]

    EXPECTED_TITLE = "Family 31 - 35 [pepper0]"
    EXPECTED_LANGUAGE = "japanese"
    EXPECTED_POSTER = "101093-101093-1960x1466.webp"
    EXPECTED_GALLERY_COUNT = 58
    EXPECTED_AUTHOR = "pepper0"

    @pytest_asyncio.fixture
    async def spider(self, session):
        if HitomiSpider.HAS_CLOUDFARE:
            pytest.skip("Сайт добавил Cloudfare")

        return HitomiSpider(session)

    @pytest.mark.asyncio
    async def test_spider_get_manga(self, manga_data):
        assert manga_data is not None

    @pytest.mark.asyncio
    async def test_spider_get_title(self, manga_data):
        assert manga_data.title == self.EXPECTED_TITLE

    @pytest.mark.asyncio
    async def test_spider_get_genres(self, manga_data):
        for tag in self.TAGS:
            assert tag in manga_data.genres

    @pytest.mark.asyncio
    async def test_spider_get_language(self, manga_data):
        assert manga_data.language == self.EXPECTED_LANGUAGE

    @pytest.mark.asyncio
    async def test_spider_get_poster(self, manga_data):
        assert self.EXPECTED_POSTER in str(manga_data.poster)

    @pytest.mark.asyncio
    async def test_spider_get_gallery(self, manga_data):
        assert len(manga_data.gallery) == self.EXPECTED_GALLERY_COUNT

    @pytest.mark.asyncio
    async def test_spider_get_author(self, manga_data):
        assert manga_data.author == self.EXPECTED_AUTHOR

    @pytest.mark.asyncio
    async def test_spider_run(self, spider):
        with pytest.raises(AttributeError):
            await spider.run()


class TestSpiderHentaiEra(BaseSpiderTest):
    BASE_URL = "https://hentaiera.com"
    TEST_URL = "https://hentaiera.com/gallery/1605408/"

    TAGS = [
        "lolicon",
        "uncensored",
        "group",
        "anal",
        "double penetration",
        "unusual pupils",
    ]

    EXPECTED_TITLE = "(C95) [Bloody Okojo (Mojyako)] PINK! (Sword Art Online Alternative Gun Gale Online) [English] [Black Grimoires] [Decensored]"
    EXPECTED_LANGUAGE = "english"
    EXPECTED_POSTER = "cover.jpg"
    EXPECTED_GALLERY_COUNT = 43
    EXPECTED_AUTHOR = "mojyako"

    @pytest_asyncio.fixture
    async def spider(self, session):
        if HentaiEraSpider.HAS_CLOUDFARE:
            pytest.skip("Сайт добавил Cloudfare")

        return HentaiEraSpider(session)

    @pytest.mark.asyncio
    async def test_spider_get_manga(self, manga_data):
        assert manga_data is not None

    @pytest.mark.asyncio
    async def test_spider_get_title(self, manga_data):
        assert manga_data.title == self.EXPECTED_TITLE

    @pytest.mark.asyncio
    async def test_spider_get_genres(self, manga_data):
        for tag in self.TAGS:
            assert tag in manga_data.genres

    @pytest.mark.asyncio
    async def test_spider_get_language(self, manga_data):
        assert manga_data.language == self.EXPECTED_LANGUAGE

    @pytest.mark.asyncio
    async def test_spider_get_poster(self, manga_data):
        assert self.EXPECTED_POSTER in str(manga_data.poster)

    @pytest.mark.asyncio
    async def test_spider_get_gallery(self, manga_data):
        assert len(manga_data.gallery) == self.EXPECTED_GALLERY_COUNT

    @pytest.mark.asyncio
    async def test_spider_get_author(self, manga_data):
        assert manga_data.author == self.EXPECTED_AUTHOR

    @pytest.mark.asyncio
    async def test_spider_run(self, spider):
        with pytest.raises(AttributeError):
            await spider.run()
