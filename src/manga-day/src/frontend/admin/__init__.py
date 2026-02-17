import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.templating import Jinja2Templates

from ...core.manager import SpiderManager
from ...core.manager import MangaManager
from .handlers import AdminHandler

ADMIN_FILES = Path(os.path.abspath(__file__)).parent

TEMPLATES = ADMIN_FILES / "templates"
STATIC = ADMIN_FILES / "static"


def setup_admin(manager: MangaManager, spider: SpiderManager) -> APIRouter:
    templates = Jinja2Templates(TEMPLATES)
    command = AdminHandler(manager=manager, spider=spider, templates=templates)

    return command.router
