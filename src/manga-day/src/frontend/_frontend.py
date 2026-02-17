from pathlib import Path

import uvicorn

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from .user import setup_user
from .admin import setup_admin
from ..core.manager import MangaManager
from ..core.manager import SpiderManager
from ..core.service.manga import FindService
from ..core import config


def build_base_response(app: FastAPI, templates: Jinja2Templates):
    @app.exception_handler(404)
    async def not_found(request, exc):
        return templates.TemplateResponse(
            "404.html", status_code=404, context={"request": request}
        )


def setup_frontend(
    manager: MangaManager, find: FindService, spider: SpiderManager
) -> FastAPI:
    app = FastAPI(title="Manga Day", description="Сайт для просмотра мангиг")

    shared_templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

    app.include_router(setup_admin(manager, spider))
    app.include_router(setup_user(manager, find))

    build_base_response(app, shared_templates)

    return app


async def start_frontend(
    manager: MangaManager, find: FindService, spider: SpiderManager
) -> None:
    app = setup_frontend(manager, find, spider)

    _config = uvicorn.Config(
        app, host=config.api.frontend_host, port=config.api.frontend_port
    )
    server = uvicorn.Server(_config)

    await server.serve()
