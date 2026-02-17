from typing import Generic, TypeVar
from pydantic import BaseModel, Field

_T = TypeVar("_T")


class BaseResponse(BaseModel, Generic[_T]):
    """
    Базовая схема ответа
    """

    status: bool
    message: str
    result: _T | None = Field(default=None)


class CountResponse(BaseResponse[_T], Generic[_T]):
    """
    Схема ответа с количеством страниц
    """

    count: int
