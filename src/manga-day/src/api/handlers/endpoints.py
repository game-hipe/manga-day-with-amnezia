from typing import Awaitable

from fastapi import APIRouter

from ...core.manager.manga import MangaManager
from ...core.entities.schemas import (
    BaseManga,
    ApiOutputManga,
    OutputMangaSchema,
    MangaSchema,
)
from .._response import BaseResponse, CountResponse


class Endpoints:
    """Эндпоинты для API манги."""

    def __init__(self, manga_manager: MangaManager):
        """Иницилизация Endpoints

        Args:
            manga_manager (MangaManager): Менеджер манги.
        """
        self.manga_manager = manga_manager
        self._router = APIRouter(prefix="/api/v1", tags=["api"])

        self._setup_routes()

    def _setup_routes(self):
        """
        Настройка роутера добавление новых поинтов
        """
        self._router.add_api_route(
            "/pages/{page}",
            self.get_pages,
            methods=["GET"],
            response_model=CountResponse[list[BaseManga]],
            summary="Получить список манги по страницам",
            tags=["manga"],
        )

        self._router.add_api_route(
            "/manga/sku/{sku}",
            self.get_manga_by_sku,
            methods=["GET"],
            response_model=BaseResponse[ApiOutputManga | None],
            summary="Получить мангу по SKU",
            tags=["manga"],
        )

        self._router.add_api_route(
            "/manga/url/{url}",
            self.get_manga_by_url,
            methods=["GET"],
            response_model=BaseResponse[ApiOutputManga | None],
            summary="Получить мангу по URL",
            tags=["manga"],
        )

        self._router.add_api_route(
            "/manga/{id}",
            self.get_manga,
            methods=["GET"],
            response_model=BaseResponse[ApiOutputManga | None],
            summary="Получить мангу по внутреннему ID в БД",
            tags=["manga"],
        )

        self._router.add_api_route(
            "/manga/add",
            self.add_manga,
            methods=["POST"],
            response_model=BaseResponse[OutputMangaSchema | None],
            summary="Добавить мангу",
            tags=["manga"],
        )

    async def get_pages(self, page: int) -> CountResponse[list[BaseManga]]:
        """Получить страницу.

        Args:
            page (int): Номер страницы

        Returns:
            CountResponse[list[BaseManga] | None]: Результат даннных, с количеством страниц
        """
        total, result = await self.manga_manager.get_manga_pages(page)
        try:
            return CountResponse(
                status=True,
                message=f"Удалось достать {len(result)} манги",
                result=result,
                count=total,
            )

        except Exception as e:
            return CountResponse(
                status=False, message=f"Не удалось достать манги: {e}", count=0
            )

    async def get_manga_by_sku(self, sku: str) -> BaseResponse[ApiOutputManga | None]:
        """Получить страницу.

        Args:
            page (int): Номер страницы)
            sku (str):

        Returns:
            ApiOutputManga | None: Данные манги или None, если не найдена.
        """
        return await self._get_manga(self.manga_manager.get_manga_by_sku, sku)

    async def get_manga_by_url(self, url: str) -> BaseResponse[ApiOutputManga | None]:
        """Получить страницу.

        Args:
            url (str): URL манги

        Returns:
            ApiOutputManga | None: Данные манги или None, если не найдена.
        """
        return await self._get_manga(self.manga_manager.get_manga_by_url, url)

    async def get_manga(self, id: int) -> BaseResponse[ApiOutputManga | None]:
        """Получить страницу.

        Args:
            id (int): ID манги

        Returns:
            ApiOutputManga | None: Данные манги или None, если не найдена.
        """
        return await self._get_manga(self.manga_manager.get_manga, id)

    async def add_manga(
        self, manga: MangaSchema
    ) -> BaseResponse[OutputMangaSchema | None]:
        """Добавляет мангу в БД

        Args:
            manga (MangaSchema): Схема манги

        Returns:
            BaseResponse[OutputMangaSchema | None]: Возращает мангу с ID
        """
        try:
            result = await self.manga_manager.add_manga(manga)
            return BaseResponse(
                status=True, message=f"Манга добавлена, с ID {result.id}", result=result
            )
        except Exception as e:
            return BaseResponse(status=False, message=str(e))

    async def _get_manga(
        self, func: Awaitable[OutputMangaSchema | None], *args
    ) -> BaseResponse[ApiOutputManga | None]:
        """Метод для того что-бы получить мангу"""
        try:
            manga = await func(*args)
            if manga is None:
                return BaseResponse(status=False, message="Манга не найдена")
            return BaseResponse(
                status=True,
                message="Манга найдена",
                result=ApiOutputManga(**manga.as_dict()),
            )
        except Exception as e:
            return BaseResponse(status=False, message=f"Не удалось достать мангу: {e}")

    @property
    def router(self) -> APIRouter:
        """Получить роутер."""
        return self._router
