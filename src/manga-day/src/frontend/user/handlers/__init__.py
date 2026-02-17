import os

from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from ....core.manager.manga import MangaManager
from ....core.service.manga import FindService
from ....core import config


USER_FILES = Path(os.path.abspath(__file__)).parent.parent


class UserHandler:
    def __init__(
        self,
        manga_manager: MangaManager,
        templates: Jinja2Templates,
        find: FindService,
        static: Path | str | None = None,
    ):
        self._router = APIRouter(tags=["user"])
        self.find_engine = find
        self.manga_manager = manga_manager
        self.templates = templates
        self.static = Path(static) or USER_FILES / "static"
        self._setup_routes()

    def _setup_routes(self):
        self._router.add_api_route(
            "/pages/{page}",
            self.get_pages,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/static/{path:path}",
            self.get_static,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/",
            self.get_pages,
            methods=["GET"],
            tags=["frontend"],
            response_class=HTMLResponse,
        )

        self.router.add_api_route(
            "/manga/{manga_sku}",
            self.get_manga,
            tags=["frontend"],
            response_class=HTMLResponse,
            methods=["GET"],
        )

        self.router.add_api_route(
            "/manga/tags/{genre_id}",
            self.get_genres_pages,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/manga/author/{author_id}",
            self.get_author_pages,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/manga/language/{language_id}",
            self.get_language_pages,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/manga/find/{query}",
            self.get_query_pages,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

    async def get_pages(self, *, page: int = 1, request: Request) -> None:
        pages, result = await self.manga_manager.get_manga_pages(page)
        if not result:
            return self.templates.TemplateResponse(
                "404.html", status_code=404, context={"request": request}
            )

        return self.templates.TemplateResponse(
            "index.html",
            context={
                "request": request,
                "mangas": [x.as_dict() for x in result],
                "total": pages,
                "page_now": page,
            },
        )

    async def get_manga(self, *, manga_sku: str, request: Request) -> None:
        manga = await self.manga_manager.get_manga_by_sku(sku=manga_sku)

        if manga is None:
            return self.templates.TemplateResponse(
                "404.html", status_code=404, context={"request": request}
            )

        return self.templates.TemplateResponse(
            "manga.html",
            context={
                "request": request,
                "manga": manga.as_dict(),
                "bot": config.user_bot.url,
            },
        )

    async def get_genres_pages(
        self, *, genre_id: int, page: int = 1, request: Request
    ) -> None:
        pages, result = await self.find_engine.get_pages_by_genre(genre_id, page)
        genre = await self.find_engine.get(genre_id, "genre")
        if not result:
            return self.templates.TemplateResponse(
                "not_found.html", status_code=404, context={"request": request}
            )

        return self.templates.TemplateResponse(
            "index.html",
            context={
                "request": request,
                "mangas": [x.as_dict() for x in result],
                "total": pages,
                "page_now": page,
                "title": "[Жанр] - " + (genre or "Неизвестный"),
            },
        )

    async def get_author_pages(
        self, *, author_id: int, page: int = 1, request: Request
    ) -> None:
        pages, result = await self.find_engine.get_pages_by_author(author_id, page)
        author = await self.find_engine.get(author_id, "author")
        if not result:
            return self.templates.TemplateResponse(
                "not_found.html", status_code=404, context={"request": request}
            )

        return self.templates.TemplateResponse(
            "index.html",
            context={
                "request": request,
                "mangas": [x.as_dict() for x in result],
                "total": pages,
                "page_now": page,
                "title": "[Автор] - " + (author or "Неизвестный"),
            },
        )

    async def get_language_pages(
        self, *, language_id: int, page: int = 1, request: Request
    ) -> None:
        pages, result = await self.find_engine.get_pages_by_language(language_id, page)
        language = await self.find_engine.get(language_id, "language")
        if not result:
            return self.templates.TemplateResponse(
                "not_found.html", status_code=404, context={"request": request}
            )

        return self.templates.TemplateResponse(
            "index.html",
            context={
                "request": request,
                "mangas": [x.as_dict() for x in result],
                "total": pages,
                "page_now": page,
                "title": "[Язык] - " + (language or "Неизвестный"),
            },
        )

    async def get_query_pages(
        self, *, query: str, page: int = 1, request: Request
    ) -> None:
        pages, result = await self.find_engine.get_pages_by_query(query, page)
        if not result:
            result = await self.find_engine.manager.get_manga_by_sku(query)
            if not result:
                return self.templates.TemplateResponse(
                    "not_found.html", status_code=404, context={"request": request}
                )
            else:
                return self.templates.TemplateResponse(
                    "manga.html",
                    context={
                        "request": request,
                        "manga": result.as_dict(),
                        "bot": config.user_bot.url,
                    },
                )

        return self.templates.TemplateResponse(
            "index.html",
            context={
                "request": request,
                "mangas": [x.as_dict() for x in result],
                "total": pages,
                "page_now": page,
                "title": query,
            },
        )

    async def get_static(self, path: str) -> FileResponse:
        static_file = self.static / path
        if static_file.exists():
            return FileResponse(static_file)
        raise HTTPException(status_code=404)

    @property
    def router(self) -> APIRouter:
        return self._router
