import asyncio

from pathlib import Path
from typing import NoReturn

from loguru import logger
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from ....core import config
from ....core.manager import MangaManager, SpiderManager
from ....core.manager.spider import SpiderStatus
from .._alert import AdminAlert
from .schemas import ParsingSignal, SpiderResponse

STATIC = Path(__file__).parent.parent / "static"


class AdminHandler:
    def __init__(
        self,
        manager: MangaManager,
        spider: SpiderManager,
        templates: Jinja2Templates,
        static: Path | str | None = None,
    ):
        self._latest = None
        self._router = APIRouter(prefix="/admin")
        self.manager = manager
        self.spider = spider

        self.static = Path(static or STATIC)
        self.templates = templates

        self._setup_routers()

    def _setup_routers(self):
        self.router.add_api_route(
            "/",
            self.index,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["admin"],
        )

        self.router.add_api_route(
            "/static/{path:path}",
            self.get_static,
            methods=["GET"],
            response_class=FileResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/command", self.spider_starter, methods=["POST"], tags=["admin"]
        )

        self.router.add_api_route(
            "/spiders", self.get_spiders, tags=["admin"], methods=["GET"]
        )

        self.router.add_api_websocket_route("/ws", self.status_socket)

    async def index(self, request: Request):
        return self.templates.TemplateResponse(
            "index.html", context={"request": request, "port": config.api.frontend_port}
        )

    async def get_spiders(self) -> list[SpiderStatus]:
        return self.spider.status

    async def status_socket(self, websocket: WebSocket) -> NoReturn:
        await websocket.accept()
        alert = AdminAlert(websocket)
        self.spider.alert.add_alert(alert)

        async def send_status():
            try:
                self._latest = self._spider_status
                await websocket.send_json(
                    SpiderResponse(
                        result=[x.as_dict() for x in self.spider.status]
                    ).model_dump()
                )
                while True:
                    if self._latest != self._spider_status:
                        await websocket.send_json(
                            SpiderResponse(
                                result=[x.as_dict() for x in self.spider.status]
                            ).model_dump()
                        )
                        self._latest = self._spider_status

                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                logger.info("Отключение системы.")

            except WebSocketDisconnect:
                logger.debug("Пользователь отключился")

            finally:
                if not websocket.client_state == WebSocketState.DISCONNECTED:
                    try:
                        await websocket.close()
                    except RuntimeError:
                        pass

        try:
            await send_status()
        except RuntimeError:
            pass
        finally:
            self.spider.alert.remove_alert(alert)

    async def spider_starter(
        self, signal: ParsingSignal
    ) -> SpiderStatus | list[SpiderStatus]:
        if signal.signal == "start":
            if signal.spider == "all":
                asyncio.create_task(self.spider.start_full_parsing())
                await asyncio.sleep(signal.timeout)
                return self.spider.status

            asyncio.create_task(
                self.spider.starter.start_spider(signal.spider, signal.page)
            )
            await asyncio.sleep(signal.timeout)
            return self.spider.get_spider_status(signal.spider)

        else:
            if signal.spider == "all":
                asyncio.create_task(self.spider.stop_all_spider())
                await asyncio.sleep(signal.timeout)
                return self.spider.status

            asyncio.create_task(self.spider.starter.stop_spider(signal.spider))
            await asyncio.sleep(signal.timeout)
            return self.spider.get_spider_status(signal.spider)

    async def get_static(self, path: str) -> FileResponse:
        static_file = self.static / path
        if static_file.exists():
            return FileResponse(static_file)
        raise HTTPException(status_code=404)

    @property
    def router(self) -> APIRouter:
        return self._router

    @property
    def _spider_status(self):
        return "\n".join(str(x) for x in self.spider.status)
