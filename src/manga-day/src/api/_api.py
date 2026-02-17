import uvicorn

from fastapi import FastAPI

from .handlers.endpoints import Endpoints
from ..core.manager.manga import MangaManager
from ..core import config


def setup_api(manager: MangaManager) -> FastAPI:
    """Инцилизация API

    Args:
        manager (MangaManager): Менеджер манги

    Returns:
        FastAPI: Обьект FastAPI
    """
    app = FastAPI(title="Manga-Day API")

    endpoint = Endpoints(manager)
    app.include_router(endpoint.router)

    return app


async def start_api(manager: MangaManager) -> None:
    """Запускает API.

    Args:
        manager (MangaManager): Менеджер манги
    """
    app = setup_api(manager)

    _config = uvicorn.Config(
        app, host=config.api.backend_host, port=config.api.backend_port
    )

    server = uvicorn.Server(_config)
    await server.serve()
