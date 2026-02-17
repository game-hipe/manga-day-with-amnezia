from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Any, Awaitable


class AdminMiddleware(BaseMiddleware):
    """
    Мидлварь для проверки прав администратора.
    Проверяет, что пользователь является администратором.
    """

    def __init__(self, admin_ids: list[int]):
        super().__init__()
        self.admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if event.from_user.id not in self.admin_ids:
            await event.answer(
                f"У вас нет прав администратора!\nВаш ID: <code>{event.from_user.id}</code>"
            )
            return

        return await handler(event, data)
