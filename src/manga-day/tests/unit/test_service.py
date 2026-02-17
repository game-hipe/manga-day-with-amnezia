import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from src.core.manager.manga import MangaManager
from src.core.service.manga import FindService
from src.core.entities.models import Manga
from src.core.entities.schemas import MangaSchema


db_path = "test_templates/test-service-database.db"
mangas_path = "test_templates/mangas.json"


class TestService:
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
    def mangas(self):
        result = []
        with open(mangas_path, encoding="utf-8") as f:
            for manga in json.load(f):
                result.append(MangaSchema(**manga))

        return result

    @pytest.fixture
    def service(self, database):
        return FindService(database)

    @pytest.mark.asyncio
    async def test_add(self, database, mangas):
        for manga in mangas:
            await database.add_manga(manga)

    @pytest.mark.asyncio
    async def test_find(self, service):
        mangas = await service.get_pages_by_query(
            "секс",  # Title,
            1,  # Page
        )

        assert len(mangas[1]) == 6
        assert mangas[0] == 1

    @pytest.mark.asyncio
    async def test_find_genre(self, service):
        mangas = await service.get_pages_by_genre(
            1,  # Genre ID
            1,  # PAGE
        )

        assert len(mangas[1]) == 30
        assert mangas[0] == 4

    @pytest.mark.asyncio
    async def test_find_author(self, service):
        mangas = await service.get_pages_by_author(
            27,  # Author ID
            1,  # PAGE
        )

        assert len(mangas[1]) == 1
        assert mangas[0] == 1

    @pytest.mark.asyncio
    async def test_find_language(self, service):
        mangas = await service.get_pages_by_language(
            1,  # Language ID
            1,  # PAGE
        )

        assert len(mangas[1]) == 30
        assert mangas[0] == 4

    @pytest.mark.asyncio
    async def test_check_error(self, service):
        with pytest.raises(ValueError):
            await service.get_pages_by_query(
                "",  # Title,
                1,  # Page
            )

        with pytest.raises(ValueError):
            await service.get_pages_by_query(
                "Секс",  # Title,
                0,  # Page
            )

        with pytest.raises(ValueError):
            await service.get_pages_by_genre(
                1,  # Genre ID
                1,  # PAGE
                -1,
            )
