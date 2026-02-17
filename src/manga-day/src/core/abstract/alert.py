from typing import TypeAlias, Literal
from abc import ABC, abstractmethod

LEVEL: TypeAlias = Literal["info", "warning", "error", "critical"]


class BaseAlert(ABC):
    """
    Абстрактный класс для отправки уведомлений.
    """

    @abstractmethod
    async def alert(self, message: str, level: LEVEL) -> bool:
        """
        Отправляет уведомление.
        Args:
            message (str): Сообщение для отправки
            level (LEVEL): Уровень сообщение ["info" "warning" "error" "critical"]
        Returns:
            bool: True, если уведомление отправлено успешно, иначе False. Если
            уведомление не отправлено, то система алёртов будет удалена
        """
