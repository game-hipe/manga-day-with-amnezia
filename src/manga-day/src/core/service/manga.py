import asyncio
import math

from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from loguru import logger

from ..entities.schemas import BaseManga
from ..entities.models import Genre, GenreManga, Language, Author, Manga
from ..manager.manga import MangaManager


class FindService:
    BASE_PER_PAGE: int = 30

    def __init__(self, manager: MangaManager):
        self.manager = manager

    async def get_pages_by_genre(
        self, genre_id: int, page: int, per_page: int | None = None
    ) -> tuple[int, list[BaseManga]]:
        """
        Получает список страниц манги по жанру.

        Args:
            genre_id (int): ID жанра.

        Returns:
            list[BaseManga]: Список манги.

        Raises:
            ValueError: Если номер страницы меньше 1.
            ValueError: Если количество манги на странице меньше 1.
        """
        per_page = per_page or self.BASE_PER_PAGE
        if page < 1:
            logger.error(f"Неверный номер страницы (page={page})")
            raise ValueError("Неверный номер страницы")

        if per_page < 1:
            logger.error(f"Неверное количество манги на странице (per_page={per_page})")
            raise ValueError("Неверное количество манги на странице")

        async with self.manager.Session() as session:
            base_query = select(GenreManga).where(GenreManga.genre_id == genre_id)

            async def scalars_manga():
                async with self.manager.Session() as manga_session:
                    query = (
                        base_query.options(selectinload(GenreManga.manga))
                        .offset((page - 1) * (per_page))
                        .limit(per_page)
                        .order_by(desc(GenreManga.id))
                    )
                    mangas = await manga_session.scalars(query)

                    if not mangas:
                        logger.warning(
                            f"Манга не найдена (genre_id={genre_id}, page={page})"
                        )
                        return []

                    return [
                        BaseManga(title=manga.title, poster=manga.poster, url=manga.url)
                        for manga in [x.manga for x in mangas]
                    ]

            total, result = await asyncio.gather(
                session.scalar(select(func.count()).select_from(base_query.subquery())),
                scalars_manga(),
            )

            return math.ceil((total or 0) / per_page), result

    async def get_pages_by_author(
        self, author_id: int, page: int, per_page: int | None = None
    ) -> tuple[int, list[BaseManga]]:
        """
        Получает список страниц манги по автору.

        Args:
            author_id (int): ID автора.

        Returns:
            list[BaseManga]: Список манги.

        Raises:
            ValueError: Если номер страницы меньше 1.
            ValueError: Если количество манги на странице меньше 1.
        """
        per_page = per_page or self.BASE_PER_PAGE

        if page < 1:
            logger.error(f"Неверный номер страницы (page={page})")
            raise ValueError("Неверный номер страницы")

        if per_page < 1:
            logger.error(f"Неверное количество манги на странице (per_page={per_page})")
            raise ValueError("Неверное количество манги на странице")

        async with self.manager.Session() as session:
            base_query = select(Manga).where(Manga.author_id == author_id)

            async def scalars_manga():
                async with self.manager.Session() as manga_session:
                    query = (
                        base_query.offset((page - 1) * (per_page))
                        .limit(per_page)
                        .order_by(desc(Manga.id))
                    )
                    mangas = await manga_session.scalars(query)
                    if not mangas:
                        logger.warning(
                            f"Манга не найдена (author_id={author_id}, page={page})"
                        )
                        return []

                    return [
                        BaseManga(title=manga.title, poster=manga.poster, url=manga.url)
                        for manga in mangas
                    ]

            total, result = await asyncio.gather(
                session.scalar(select(func.count()).select_from(base_query.subquery())),
                scalars_manga(),
            )

            return math.ceil((total or 0) / per_page), result

    async def get_pages_by_language(
        self, language_id: int, page: int, per_page: int | None = None
    ) -> tuple[int, list[BaseManga]]:
        """
        Получает список страниц манги по языку.

        Args:
            author_id (int): ID автора.

        Returns:
            list[BaseManga]: Список манги.

        Raises:
            ValueError: Если номер страницы меньше 1.
            ValueError: Если количество манги на странице меньше 1.
        """
        per_page = per_page or self.BASE_PER_PAGE

        if page < 1:
            logger.error(f"Неверный номер страницы (page={page})")
            raise ValueError("Неверный номер страницы")

        if per_page < 1:
            logger.error(f"Неверное количество манги на странице (per_page={per_page})")
            raise ValueError("Неверное количество манги на странице")

        async with self.manager.Session() as session:
            base_query = select(Manga).where(Manga.language_id == language_id)

            async def scalars_manga():
                async with self.manager.Session() as manga_session:
                    query = (
                        base_query.offset((page - 1) * (per_page))
                        .limit(per_page)
                        .order_by(desc(Manga.id))
                    )
                    mangas = await manga_session.scalars(query)
                    if not mangas:
                        logger.warning(
                            f"Манга не найдена (author_id={language_id}, page={page})"
                        )
                        return []

                    return [
                        BaseManga(title=manga.title, poster=manga.poster, url=manga.url)
                        for manga in mangas
                    ]

            total, result = await asyncio.gather(
                session.scalar(select(func.count()).select_from(base_query.subquery())),
                scalars_manga(),
            )

            return math.ceil((total or 0) / per_page), result

    async def get_pages_by_query(
        self, query: str, page: int, per_page: int | None = None
    ) -> tuple[int, list[BaseManga]]:
        """
        Получает список страниц манги по названию.

        Args:
            author_id (int): ID автора.

        Returns:
            list[BaseManga]: Список манги.

        Raises:
            ValueError: Если номер страницы меньше 1.
            ValueError: Если количество манги на странице меньше 1.
        """
        logger.debug(
            f"Поиск манги по запросу: {query} (page={page}, per_page={per_page})"
        )

        per_page = per_page or self.BASE_PER_PAGE

        if not query:
            logger.error(f"Неверный запрос (query={query})")
            raise ValueError("Неверный запрос")

        if page < 1:
            logger.error(f"Неверный номер страницы (page={page})")
            raise ValueError("Неверный номер страницы")

        if per_page < 1:
            logger.error(f"Неверное количество манги на странице (per_page={per_page})")
            raise ValueError("Неверное количество манги на странице")

        async with self.manager.Session() as session:
            base_query = select(Manga).where(
                func.lower(Manga.title).contains(query.lower())
            )

            async def scalars_manga():
                async with self.manager.Session() as session:
                    find_query = (
                        base_query.offset((page - 1) * (per_page))
                        .limit(per_page)
                        .order_by(desc(Manga.id))
                    )
                    mangas = await session.scalars(find_query)
                    if not mangas:
                        logger.warning(f"Манга не найдена (query={query}, page={page})")
                        return []

                    return [
                        BaseManga(title=manga.title, poster=manga.poster, url=manga.url)
                        for manga in mangas
                    ]

            total, result = await asyncio.gather(
                session.scalar(select(func.count()).select_from(base_query.subquery())),
                scalars_manga(),
            )

            return math.ceil((total or 0) / per_page), result

    async def get(self, id: int, param: str) -> str | None:
        model = None
        if "genre" == param:
            model = Genre
        elif "author" == param:
            model = Author
        elif "language" == param:
            model = Language
        else:
            raise ValueError(f"Неверный параметр: {param}")

        async with self.manager.Session() as session:
            result = await session.get(model, id)
            if result is None:
                logger.warning(f"Объект не найден (id={id}, param={param})")
                return None
            else:
                return result.name
