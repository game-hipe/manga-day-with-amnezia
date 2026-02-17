import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from src.core.manager.manga import MangaManager
from src.core.entities.schemas import MangaSchema, OutputMangaSchema
from src.core.entities.models import Manga


ADDEDMANGA_ID: int = None
db_path = "test_templates/test-database.db"


class TestAddMangaTest:
    @pytest_asyncio.fixture(scope="session")
    async def engine(self):
        """Создание асинхронного движка для тестовой БД"""

        if os.path.exists(db_path):
            os.remove(db_path)

        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")

        try:
            async with engine.begin() as conn:
                await conn.run_sync(Manga.metadata.create_all)

            yield engine

        finally:
            await engine.dispose()
            if os.path.exists(db_path):
                os.remove(db_path)

    @pytest_asyncio.fixture
    async def database(self, engine):
        return MangaManager(engine)

    @pytest.fixture
    def manga(self):
        return MangaSchema(
            title="Test Manga 1",
            poster="https://example.com/poster.jpg",
            url="https://example.com/manga/1",
            genres=["ahegao", "simple sex"],
            author="Test Author",
            language="English",
            gallery=[
                "https://example.com/gallery/1.jpg",
                "https://example.com/gallery/2.jpg",
            ],
        )

    @pytest.fixture
    def manga_without_genres(self):
        return MangaSchema(
            title="Test Manga 2",
            poster="https://example.com/poster.jpg",
            url="https://example.com/manga/2",
            author="Test Author",
            language="English",
            gallery=[
                "https://example.com/gallery/1.jpg",
                "https://example.com/gallery/2.jpg",
            ],
        )

    @pytest.fixture
    def manga_without_author(self):
        return MangaSchema(
            title="Test Manga 3",
            poster="https://example.com/poster.jpg",
            url="https://example.com/manga/3",
            genres=["ahegao", "simple sex"],
            language="English",
            gallery=[
                "https://example.com/gallery/1.jpg",
                "https://example.com/gallery/2.jpg",
            ],
        )

    @pytest.fixture
    def manga_without_lanugaue(self):
        return MangaSchema(
            title="Test Manga 4",
            poster="https://example.com/poster.jpg",
            url="https://example.com/manga/4",
            genres=["ahegao", "simple sex"],
            gallery=[
                "https://example.com/gallery/1.jpg",
                "https://example.com/gallery/2.jpg",
            ],
        )

    @pytest.mark.asyncio
    async def test_add_manga(self, database, manga):
        global ADDEDMANGA_ID
        result = await database.add_manga(manga)

        ADDEDMANGA_ID = result.id
        assert isinstance(result.id, int)

    @pytest.mark.asyncio
    async def test_get_manga(self, database):
        if ADDEDMANGA_ID is not None:
            result = await database.get_manga(ADDEDMANGA_ID)
            assert isinstance(result, OutputMangaSchema)
        else:
            assert False

    @pytest.mark.asyncio
    async def test_get_manga_title(self, database):
        if ADDEDMANGA_ID is None:
            assert False

        result = await database.get_manga(ADDEDMANGA_ID)
        assert result.title == "Test Manga 1"

    @pytest.mark.asyncio
    async def test_get_manga_poster(self, database):
        if ADDEDMANGA_ID is None:
            assert False

        result = await database.get_manga(ADDEDMANGA_ID)
        assert str(result.poster) == "https://example.com/poster.jpg"

    @pytest.mark.asyncio
    async def test_get_manga_url(self, database):
        if ADDEDMANGA_ID is None:
            assert False

        result = await database.get_manga(ADDEDMANGA_ID)
        assert str(result.url) == "https://example.com/manga/1"

    @pytest.mark.asyncio
    async def test_get_manga_genres(self, database):
        if ADDEDMANGA_ID is None:
            assert False

        result = await database.get_manga(ADDEDMANGA_ID)
        assert [x.name for x in result.genres] == ["ahegao", "simple sex"]

    @pytest.mark.asyncio
    async def test_get_manga_author(self, database):
        if ADDEDMANGA_ID is None:
            assert False

        result = await database.get_manga(ADDEDMANGA_ID)
        assert result.author.name == "Test Author"

    @pytest.mark.asyncio
    async def test_get_manga_language(self, database):
        if ADDEDMANGA_ID is None:
            assert False

        result = await database.get_manga(ADDEDMANGA_ID)
        assert result.language.name == "English"

    @pytest.mark.asyncio
    async def test_get_manga_gallery(self, database):
        if ADDEDMANGA_ID is None:
            assert False

        result = await database.get_manga(ADDEDMANGA_ID)
        assert [str(x) for x in result.gallery] == [
            "https://example.com/gallery/1.jpg",
            "https://example.com/gallery/2.jpg",
        ]
        assert len(result.gallery) == 2

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "manga_fixture_name",
        [
            "manga",
            "manga_without_genres",
            "manga_without_author",
            "manga_without_lanugaue",
        ],
    )
    async def test_add_different_mangas(self, database, request, manga_fixture_name):
        """Тестирование добавления манги с разными наборами данных"""
        manga_data = request.getfixturevalue(manga_fixture_name)

        result = await database.add_manga(manga_data)

        assert isinstance(result.id, int)

        retrieved = await database.get_manga(result.id)
        assert "Test Manga" in retrieved.title
