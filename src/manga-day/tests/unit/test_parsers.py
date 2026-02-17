import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from src.spider.hmanga.parser import MangaParser as HmangaParser
from src.spider.multi_manga.parser import MangaParser as MultiMangaParser


class TestHmangaParser:
    @pytest.fixture
    def parser(self):
        return HmangaParser("https://hmanga.my/", situation="html")

    @pytest.fixture
    def sample_html(self):
        return """
        <html>
            <link rel="canonical" href="https://hmanga.my/manga/1">
            <div id="info">
                <h1>Test Manga</h1>
            </div>
            <div id="cover">
                <img data-src="/poster.jpg">
            </div>
            <section id="tags">
                <div class="tag-container">Contents
                    <a class="tag">Action</a>
                </div>
            </section>
        </html>
        """

    @pytest.mark.asyncio
    async def test_parse_valid_html(self, parser, sample_html):
        result = parser.parse(sample_html)

        assert result.title == "Test Manga"
        assert "Action" in result.genres
        assert str(result.poster) == "https://hmanga.my/poster.jpg"

    @pytest.mark.asyncio
    async def test_parse_invalid_html(self, parser):
        with pytest.raises(ValueError):
            parser.parse("<html><body>Invalid</body></html>")

    # -------------------------------------------
    # НАСТОЯЩИИЕ ДАННЫЕ
    # -------------------------------------------

    @pytest.fixture
    def tags(self):
        return [
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

    @pytest.fixture
    def real_html(self):
        with open("test_templates/hamnga-1.html", "r", encoding="utf-8") as f:
            return f.read()

    @pytest.mark.asyncio
    async def test_parse_real_html_title(self, parser, real_html):
        result = parser.parse(real_html)
        assert (
            result.title
            == "[Hagure Moguri] Ogaritai Hitozuma Kateikyoushi ~Musuko to Danna ga Inai Sabishii Seikatsu o Okutteru Naraboku no Mama ni Natte~ [Chinese]"
        )

    @pytest.mark.asyncio
    async def test_parse_real_html_genres(self, parser, real_html, tags):
        result = parser.parse(real_html)

        for tag in tags:
            assert tag in result.genres

    @pytest.mark.asyncio
    async def test_parse_real_html_lanuguage(self, parser, real_html):
        result = parser.parse(real_html)
        assert result.language == "chinese"

    @pytest.mark.asyncio
    async def test_parse_real_html_poster(self, parser, real_html):
        result = parser.parse(real_html)
        assert (
            str(result.poster)
            == "https://hmanga.my/uploads/posts/2026-01/medium/1767911442_1.webp"
        )

    @pytest.mark.asyncio
    async def test_parse_real_html_gallery(self, parser, real_html):
        result = parser.parse(real_html)
        assert len(result.gallery) == 38

    @pytest.mark.asyncio
    async def test_parse_real_html_author(self, parser, real_html):
        result = parser.parse(real_html)
        assert result.author is None


class TestMultiMangaParser:
    @pytest.fixture
    def parser(self):
        return MultiMangaParser("https://multi-manga.today", situation="html")

    @pytest.fixture
    def sample_html(self):
        return """
        <html>
            <link rel="canonical" href="https://multi-manga.today.org/manga/1">
            <div id="info">
                <h1>Test Manga</h1>
            </div>
            <div id="cover">
                <img data-src="/poster.jpg">
            </div>
            <section id="tags">
                <div class="tag-container">Теги
                    <a class="tag">Секс</a>
                </div>
            </section>
        </html>
        """

    @pytest.mark.asyncio
    async def test_parse_valid_html(self, parser, sample_html):
        result = parser.parse(sample_html)

        assert result.title == "Test Manga"
        assert "Секс" in result.genres
        assert str(result.poster) == "https://multi-manga.today/poster.jpg"

    @pytest.mark.asyncio
    async def test_parse_invalid_html(self, parser):
        with pytest.raises(ValueError):
            parser.parse("<html><body>Invalid</body></html>")

    # -------------------------------------------
    # НАСТОЯЩИИЕ ДАННЫЕ
    # -------------------------------------------

    @pytest.fixture
    def tags(self):
        return [
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

    @pytest.fixture
    def real_html(self):
        with open("test_templates/multi-manga-1.html", "r", encoding="utf-8") as f:
            return f.read()

    @pytest.mark.asyncio
    async def test_parse_real_html_title(self, parser, real_html):
        result = parser.parse(real_html)
        assert (
            result.title
            == "Моя повседневная жизнь с сестрой-грязнулей, которой нужен только секс ~Если победишь сестрёнку, то я разрешу тебе кончить без резинки!~ (Boku to Gasatsu na Onee no Seiyoku Shori Seikatsu ~Onee-chan ni Katetara Ninshin Kakugo de Nama Ecchi Hen~)"
        )

    @pytest.mark.asyncio
    async def test_parse_real_html_genres(self, parser, real_html, tags):
        result = parser.parse(real_html)

        for tag in tags:
            assert tag in result.genres

    @pytest.mark.asyncio
    async def test_parse_real_html_lanuguage(self, parser, real_html):
        result = parser.parse(real_html)
        assert result.language == "Русский"

    @pytest.mark.asyncio
    async def test_parse_real_html_poster(self, parser, real_html):
        result = parser.parse(real_html)
        assert (
            str(result.poster)
            == "https://multi-manga.today/uploads/posts/2026-01/medium/1767914666_01.webp"
        )

    @pytest.mark.asyncio
    async def test_parse_real_html_gallery(self, parser, real_html):
        result = parser.parse(real_html)
        assert len(result.gallery) == 36

    @pytest.mark.asyncio
    async def test_parse_real_html_author(self, parser, real_html):
        result = parser.parse(real_html)
        assert result.author == "Jovejun"
