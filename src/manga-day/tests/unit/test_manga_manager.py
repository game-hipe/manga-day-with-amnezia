# tests/unit/test_manga_manager.py
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.manager.manga import MangaManager
from src.core.entities.schemas import MangaSchema, BaseManga
from src.core.entities.models import Manga


db_path = "test_templates/test-manga-manager.db"


class TestMangaManager:
    @pytest_asyncio.fixture
    async def engine(self):
        """Создание асинхронного движка для тестовой БД"""
        if os.path.exists(db_path):
            os.remove(db_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")

        async with engine.begin() as conn:
            await conn.run_sync(Manga.metadata.create_all)

        try:
            yield engine
        finally:
            await engine.dispose()
            if os.path.exists(db_path):
                os.remove(db_path)

    @pytest_asyncio.fixture
    async def database(self, engine):
        return MangaManager(engine)

    @pytest.fixture
    def manga_data(self):
        return MangaSchema(
            title="Test Manga",
            poster="https://example.com/poster.jpg",
            url="https://example.com/manga/1",
            sku="manga_001",
            genres=["ahegao", "simple sex"],
            author="Test Author",
            language="English",
            gallery=[
                "https://example.com/gallery/1.jpg",
                "https://example.com/gallery/2.jpg",
            ],
        )

    @pytest.fixture
    def manga_data_1(self):
        return MangaSchema(
            title="Test Manga 1",
            poster="https://example.com/poster.jpg",
            url="https://example.com/manga/1",
            sku="manga_001",
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
            title="No Genres Manga",
            poster="https://example.com/poster2.jpg",
            url="https://example.com/manga/2",
            sku="manga_002",
            author="Another Author",
            language="Russian",
            gallery=["https://example.com/gallery/3.jpg"],
        )

    @pytest.fixture
    def manga_without_author(self):
        return MangaSchema(
            title="No Author Manga",
            poster="https://example.com/poster3.jpg",
            url="https://example.com/manga/3",
            sku="manga_003",
            genres=["comedy"],
            language="Japanese",
            gallery=["https://example.com/gallery/4.jpg"],
        )

    @pytest.fixture
    def manga_without_language(self):
        return MangaSchema(
            title="No Language Manga",
            poster="https://example.com/poster4.jpg",
            url="https://example.com/manga/4",
            sku="manga_004",
            genres=["drama"],
            author="Unknown",
            gallery=["https://example.com/gallery/5.jpg"],
        )

    # --- Тесты add_manga ---

    @pytest.mark.asyncio
    async def test_add_manga_success(self, database, manga_data):
        """Тест успешного добавления манги"""
        result = await database.add_manga(manga_data)
        assert isinstance(result.id, int)
        assert result.title == "Test Manga"
        assert str(result.url) == "https://example.com/manga/1"
        assert str(result.poster) == "https://example.com/poster.jpg"
        assert [g.name for g in result.genres] == ["ahegao", "simple sex"]
        assert result.author.name == "Test Author"
        assert result.language.name == "English"
        assert len(result.gallery) == 2

    @pytest.mark.asyncio
    async def test_add_manga_idempotent(self, database, manga_data):
        """Тест, что повторное добавление манги по SKU не создаёт дубликат"""
        result1 = await database.add_manga(manga_data)
        result2 = await database.add_manga(manga_data)

        assert result1.id == result2.id
        assert isinstance(result1.id, int)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "fixture_name",
        [
            "manga_without_genres",
            "manga_without_author",
            "manga_without_language",
        ],
    )
    async def test_add_manga_optional_fields(self, database, request, fixture_name):
        """Тест добавления манги с отсутствующими необязательными полями"""
        manga = request.getfixturevalue(fixture_name)
        result = await database.add_manga(manga)

        assert isinstance(result.id, int)
        assert "Manga" in result.title

        retrieved = await database.get_manga(result.id)
        assert retrieved is not None

        # Проверка отсутствующих полей
        if "genres" in fixture_name:
            assert retrieved.genres == []
        if "author" in fixture_name:
            assert retrieved.author is None
        if "language" in fixture_name:
            assert retrieved.language is None

    # --- Тесты get_manga ---

    @pytest.mark.asyncio
    async def test_get_manga_by_id(self, database, manga_data):
        """Тест получения манги по ID"""
        added = await database.add_manga(manga_data)
        fetched = await database.get_manga(added.id)

        assert fetched is not None
        assert fetched.id == added.id
        assert fetched.title == added.title
        assert fetched.url == added.url

    @pytest.mark.asyncio
    async def test_get_manga_not_found(self, database):
        """Тест получения несуществующей манги"""
        result = await database.get_manga(999999)
        assert result is None

    # --- Тесты get_manga_by_url / sku ---

    @pytest.mark.asyncio
    async def test_get_manga_by_url(self, database, manga_data):
        """Тест получения манги по URL"""
        await database.add_manga(manga_data)
        result = await database.get_manga_by_url(str(manga_data.url))
        assert result is not None
        assert result.title == "Test Manga"

    @pytest.mark.asyncio
    async def test_get_manga_by_sku(self, database, manga_data):
        """Тест получения манги по SKU"""
        await database.add_manga(manga_data)
        result = await database.get_manga_by_sku(manga_data.sku)
        assert result is not None
        assert result.title == "Test Manga"

    # --- Тесты in_database и get_total ---

    @pytest.mark.asyncio
    async def test_in_database(self, database, manga_data):
        """Тест проверки наличия манги в БД"""
        assert not await database.in_database(manga_data)
        await database.add_manga(manga_data)
        assert await database.in_database(manga_data)

    @pytest.mark.asyncio
    async def test_get_total(self, database, manga_data):
        """Тест подсчёта общего количества манги"""
        total_before = await database.get_total()
        await database.add_manga(manga_data)
        total_after = await database.get_total()
        assert total_after == total_before + 1

    # --- Тесты пагинации ---

    @pytest.mark.asyncio
    async def test_get_manga_pages(self, database, manga_data):
        """Тест пагинации манги"""
        # Добавим несколько манг
        for i in range(1, 5):
            md = manga_data.model_copy(
                update={
                    "title": f"Test Manga {i}",
                    "sku": f"manga_00{i}",
                    "url": f"https://example.com/manga/{i}",
                }
            )
            await database.add_manga(md)

        pages, mangas = await database.get_manga_pages(page=1, per_page=2)
        assert pages == 2  # всего 4 записи, по 2 на странице → 2 страницы
        assert len(mangas) == 2
        assert all(isinstance(m, BaseManga) for m in mangas)

    @pytest.mark.asyncio
    async def test_get_manga_pages_invalid_page(self, database):
        """Тест ошибки при неверном номере страницы"""
        with pytest.raises(ValueError, match="Неверный номер страницы"):
            await database.get_manga_pages(page=0)

    @pytest.mark.asyncio
    async def test_get_manga_pages_invalid_per_page(self, database):
        """Тест ошибки при неверном per_page"""
        with pytest.raises(ValueError, match="Неверное количество манги на странице"):
            await database.get_manga_pages(page=1, per_page=0)
