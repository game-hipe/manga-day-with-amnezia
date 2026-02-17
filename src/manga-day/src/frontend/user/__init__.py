import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.templating import Jinja2Templates

from .handlers import UserHandler
from ...core.manager.manga import MangaManager
from ...core.service.manga import FindService

USER_FILES = Path(os.path.abspath(__file__)).parent

TEMPLATES = USER_FILES / "templates"
STATIC = USER_FILES / "static"


def setup_user(manager: MangaManager, find: FindService) -> APIRouter:
    templates = Jinja2Templates(TEMPLATES)
    router = APIRouter()

    user_router = UserHandler(
        manga_manager=manager, templates=templates, find=find, static=STATIC
    )

    router.include_router(user_router.router)

    return router
