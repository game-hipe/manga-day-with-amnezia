from ...core.abstract.alert import BaseAlert, LEVEL
from .handlers.schemas import MessageResponse
from fastapi.websockets import WebSocket, WebSocketState


class AdminAlert(BaseAlert):
    def __init__(self, wb: WebSocket):
        self._wb = wb

    async def alert(self, message: str, level: LEVEL) -> bool:
        try:
            if self.is_closed():
                return False

            await self._wb.send_json(
                MessageResponse(
                    result={"message": message, "level": level}
                ).model_dump()
            )
            return True
        except Exception:
            return False

    def is_closed(self):
        return self._wb.client_state == WebSocketState.DISCONNECTED
