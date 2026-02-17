import asyncio
import math
from typing import overload

from sqlalchemy import func, desc

from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncEngine
from loguru import logger

from ..entities.schemas import (
    MangaSchema,
    OutputMangaSchema,
    BaseManga,
    ObjectWithId,
)
from ..entities.models import (
    Manga,
    Gallery,
    Language,
    Author,
    GenreManga,
    Genre,
    GeneratedPdf,
)


class MangaManager:
    """
    Менеджер для асинхронной работы с данными манги в базе данных.

    Предоставляет методы для добавления, получения и фильтрации манги,
    а также взаимодействия с авторами, жанрами, языками и галереями.
    Использует SQLAlchemy для асинхронного доступа к базе данных.

    Атрибуты:
        BASE_PER_PAGE (int): Количество манги на одной странице по умолчанию.
    """

    BASE_PER_PAGE: int = 30

    def __init__(self, engine: AsyncEngine):
        """
        Инициализирует менеджер манги.

        Args:
            engine (AsyncEngine): Асинхронный движок SQLAlchemy для подключения к БД.
        """
        self._engine = engine
        self.Session: async_sessionmaker[AsyncSession] = async_sessionmaker(engine)

    async def add_manga(self, manga: MangaSchema) -> OutputMangaSchema:
        """
        Добавляет новую мангу в базу данных.

        При необходимости создаёт или получает существующие записи:
        язык, автор, жанры, галерея. Связывает их с мангой.

        Args:
            manga (MangaSchema): Схема данных новой манги.

        Returns:
            OutputMangaSchema: Добавленная манга с заполненными ID и связями. OutputMangaSchema, если манга уже существует.
        """
        async with self.Session() as session:
            async with session.begin():
                find_manga = await session.scalar(
                    select(Manga)
                    .where(Manga.sku == manga.sku)
                    .options(
                        joinedload(Manga.author),
                        joinedload(Manga.language),
                        selectinload(Manga.genres_connection).joinedload(
                            GenreManga.genre
                        ),
                        joinedload(Manga.gallery),
                    )
                    .execution_options(populate_existing=True)
                )
                if find_manga is not None:
                    logger.warning(f"Манга уже существует (sku={find_manga.sku})")
                    return self._build_manga(find_manga, id=find_manga.id)

                title = manga.title
                url = str(manga.url)
                poster = str(manga.poster)

                language = None
                author = None

                if manga.language:
                    language = await self._add_language(session, manga.language)

                if manga.author:
                    author = await self._add_author(session, manga.author)

                result = Manga(
                    title=title,
                    url=url,
                    poster=poster,
                    language_id=language.id if language is not None else None,
                    author_id=author.id if author is not None else None,
                )
                session.add(result)
                await session.flush()

                genres = await self._connect(result, manga, session)

                return OutputMangaSchema(
                    title=manga.title,
                    poster=manga.poster,
                    url=manga.url,
                    genres=genres,
                    author=ObjectWithId(name=manga.author, id=author.id)
                    if author
                    else None,
                    language=ObjectWithId(name=manga.language, id=language.id)
                    if language
                    else None,
                    gallery=manga.gallery,
                    id=result.id,
                )

    async def get_manga(self, id: int) -> OutputMangaSchema | None:
        """
        Получает мангу по её идентификатору.

        Загружает все связанные данные: автора, язык, жанры, галерею.

        Args:
            id (int): Уникальный идентификатор манги.

        Returns:
            OutputMangaSchema | None: Данные манги или None, если не найдена.
        """
        async with self.Session() as session:
            manga = await session.scalar(
                select(Manga)
                .where(Manga.id == id)
                .options(
                    joinedload(Manga.author),
                    joinedload(Manga.language),
                    selectinload(Manga.genres_connection).joinedload(GenreManga.genre),
                    joinedload(Manga.gallery),
                    joinedload(Manga.generated_pdf),
                )
                .execution_options(populate_existing=True)
            )
            if manga is None:
                logger.warning(f"Манга не найдена (id={id})")
                return None

            return self._build_manga(
                manga,
                id=manga.id,
                pdf_id=manga.generated_pdf.id_file if manga.generated_pdf else None,
            )

    async def get_manga_by_url(self, url: str) -> OutputMangaSchema | None:
        """
        Получает мангу по её URL.

        Загружает все связанные данные: автора, язык, жанры, галерею.

        Args:
            url (str): URL манги.

        Returns:
            OutputMangaSchema | None: Данные манги или None, если не найдена.
        """
        async with self.Session() as session:
            manga = await session.scalar(
                select(Manga)
                .where(Manga.url == url)
                .options(
                    joinedload(Manga.author),
                    joinedload(Manga.language),
                    selectinload(Manga.genres_connection).joinedload(GenreManga.genre),
                    joinedload(Manga.gallery),
                    joinedload(Manga.generated_pdf),
                )
                .execution_options(populate_existing=True)
            )
            if manga is None:
                logger.warning(f"Манга не найдена (url={url})")
                return None

            return self._build_manga(
                manga,
                id=manga.id,
                pdf_id=manga.generated_pdf.id_file if manga.generated_pdf else None,
            )

    async def get_manga_by_sku(self, sku: str) -> OutputMangaSchema | None:
        """
        Получает мангу по её SKU.

        Загружает все связанные данные: автора, язык, жанры, галерею.

        Args:
            sku (str): sku манги.

        Returns:
            OutputMangaSchema | None: Данные манги или None, если не найдена.
        """
        async with self.Session() as session:
            manga = await session.scalar(
                select(Manga)
                .where(Manga.sku == sku)
                .options(
                    joinedload(Manga.author),
                    joinedload(Manga.language),
                    selectinload(Manga.genres_connection).joinedload(GenreManga.genre),
                    joinedload(Manga.gallery),
                    joinedload(Manga.generated_pdf),
                )
                .execution_options(populate_existing=True)
            )
            if manga is None:
                logger.warning(f"Манга не найдена (sku={sku})")
                return None

            return self._build_manga(
                manga,
                id=manga.id,
                pdf_id=manga.generated_pdf.id_file if manga.generated_pdf else None,
            )

    async def get_manga_pages(
        self, page: int, per_page: int | None = None
    ) -> tuple[int, list[BaseManga]]:
        """
        Получает список манги для указанной страницы.

        Args:
            page (int): Номер страницы (начинается с 1).
            per_page (int | None): Количество манги на странице. По умолчанию — BASE_PER_PAGE.

        Raises:
            ValueError: Если номер страницы меньше 1.
            ValueError: Если количество манги на странице меньше 1.

        Returns:
            list[BaseManga]: Список манги без детальной информации.
        """
        per_page = per_page if per_page is not None else self.BASE_PER_PAGE

        if page < 1:
            logger.error(f"Неверный номер страницы (page={page})")
            raise ValueError("Неверный номер страницы")

        if per_page < 1:
            logger.error(f"Неверное количество манги на странице (per_page={per_page})")
            raise ValueError("Неверное количество манги на странице")

        async with self.Session() as session:

            async def get_page():
                async with self.Session() as session_page:
                    if result := await session_page.scalars(
                        select(Manga)
                        .offset((page - 1) * (per_page))
                        .limit(per_page)
                        .order_by(desc(Manga.id))
                    ):
                        return [
                            BaseManga(
                                title=manga.title, poster=manga.poster, url=manga.url
                            )
                            for manga in result
                        ]

                    logger.warning(f"Манга не найдена (page={page})")
                    return []

            total, r = await asyncio.gather(
                session.scalar(select(func.count()).select_from(Manga)),
                get_page(),
            )

            return math.ceil(total / per_page), r

    async def add_pdf(self, file_id: int, manga_id: int) -> None:
        """Добавляет связь PDF для манги

        Args:
            file_id (int): file_id для ТГ бота (На данный момент доступно только сохранение в ТГ боте)
            manga_id (int): ID манги к которому сохранена запись
        """
        async with self.Session() as session:
            async with session.begin():
                if await session.scalar(
                    select(GeneratedPdf).where(GeneratedPdf.id_manga == manga_id)
                ):
                    logger.warning("PDF - для этой манги уже добавлен!")
                    return

                obj = GeneratedPdf(id_file=file_id, id_manga=manga_id)
                session.add(obj)

            logger.info(
                f"Запись PDF добавлена (file_id={file_id}, manga_id={manga_id})"
            )

    async def in_database(self, manga: BaseManga) -> bool:
        async with self.Session() as session:
            db_manga = None
            try:
                db_manga = await session.scalar(
                    select(Manga).where(Manga.sku == manga.sku)
                )
                if db_manga:
                    return True

                return False
            finally:
                if db_manga is not None and db_manga.poster != str(manga.poster):
                    db_manga.poster = str(manga.poster)
                    await session.commit()

    async def get_total(self) -> int:
        async with self.Session() as session:
            total = await session.scalar(select(func.count()).select_from(Manga))
            return total or 0

    async def _connect(
        self, manga: Manga, manga_schema: MangaSchema, session: AsyncSession
    ) -> list[ObjectWithId]:
        """
        Связывает мангу с жанрами и галереей.

        Создаёт записи в таблицах связи и добавляет галерею.

        Args:
            manga (Manga): Объект манги из БД.
            manga_schema (MangaSchema): Входные данные манги.
            session (AsyncSession): Активная сессия БД.

        Returns:
            list[ObjectWithId]: Список связанных объектов.

        """
        result: list[ObjectWithId] = []
        for genre_name in manga_schema.genres:
            genre = await self._add_genre(session, genre_name)
            session.add(GenreManga(genre_id=genre.id, manga_id=manga.id))
            result.append(ObjectWithId(id=genre.id, name=genre.name))

        gallery = Gallery(
            urls=[str(x) for x in manga_schema.gallery], manga_id=manga.id
        )
        session.add(gallery)
        return result

    async def _add_author(self, session: AsyncSession, author: str) -> Author:
        """
        Добавляет автора в БД или возвращает существующего.

        Args:
            session (AsyncSession): Активная сессия БД.
            author (str): Имя автора.

        Returns:
            Author: Объект автора.
        """
        return await self._add_item(session, Author, author)

    async def _add_genre(self, session: AsyncSession, genre: str) -> Genre:
        """
        Добавляет жанр в БД или возвращает существующий.

        Args:
            session (AsyncSession): Активная сессия БД.
            genre (str): Название жанра.

        Returns:
            Genre: Объект жанра.
        """
        return await self._add_item(session, Genre, genre)

    async def _add_language(self, session: AsyncSession, language: str) -> Language:
        """
        Добавляет язык в БД или возвращает существующий.

        Args:
            session (AsyncSession): Активная сессия БД.
            language (str): Название языка.

        Returns:
            Language: Объект языка.
        """
        return await self._add_item(session, Language, language)

    async def _add_item(
        self, session: AsyncSession, model: type[Author | Genre | Language], item: str
    ) -> Author | Genre | Language:
        """
        Универсальный метод для добавления сущности (автор, жанр, язык).

        Проверяет наличие записи по имени, при отсутствии создаёт новую.

        Args:
            session (AsyncSession): Активная сессия БД.
            model (type[Author | Genre | Language]): Модель сущности.
            item (str): Имя сущности.

        Returns:
            Author | Genre | Language: Найденная или созданная сущность.
        """
        if result := await session.scalar(select(model).where(model.name == item)):
            return result

        result = model(name=item)
        session.add(result)
        await session.flush()
        return result

    @overload
    def _build_manga(self, manga: Manga, id: int) -> OutputMangaSchema: ...

    @overload
    def _build_manga(
        self, manga: OutputMangaSchema, language_id: int, author_id: int
    ) -> Manga: ...

    def _build_manga(
        self, manga: Manga | OutputMangaSchema, **kw
    ) -> OutputMangaSchema | Manga:
        """
        Преобразует объект между моделью БД и выходной схемой.

        Перегруженная функция:
         - Из Manga -> OutputMangaSchema
         - Из OutputMangaSchema -> Manga

        Args:
            manga (Manga | OutputMangaSchema): Входной объект.
            **kw: Дополнительные поля (например, id, language_id, author_id).

        Returns:
            OutputMangaSchema | Manga: Преобразованный объект.
        """
        if isinstance(manga, Manga):
            return OutputMangaSchema(
                title=manga.title,
                poster=manga.poster,
                url=manga.url,
                genres=[
                    ObjectWithId(name=genre.name, id=genre.id) for genre in manga.genres
                ],
                author=ObjectWithId(name=manga.author.name, id=manga.author_id)
                if manga.author
                else None,
                language=ObjectWithId(name=manga.language.name, id=manga.language_id)
                if manga.language
                else None,
                gallery=manga.gallery.urls,
                **kw,
            )
        elif isinstance(manga, OutputMangaSchema):
            return Manga(
                title=manga.title, url=str(manga.url), poster=str(manga.poster), **kw
            )
