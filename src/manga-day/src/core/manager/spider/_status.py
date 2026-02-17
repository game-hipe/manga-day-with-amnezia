from enum import Enum

from pydantic import BaseModel


class SpiderStatusEnum(Enum):
    """
    Статусы спайдера
    """

    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"
    NOT_RUNNING = "not_running"
    RUNNING = "running"
    CANCELLED = "cancelled"


class SpiderStatus(BaseModel):
    name: str
    status: SpiderStatusEnum
    message: str | None

    def __str__(self) -> str:
        return (
            f"[<b>{self.name}</b>] - <b>{self.status.value}</b>" + f" | {self.message}"
            if self.message
            else ""
        )

    def as_dict(self) -> dict:
        return {"name": self.name, "status": self.status.value, "message": self.message}
