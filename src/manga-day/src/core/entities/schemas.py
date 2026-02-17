import hashlib

from aiohttp import BasicAuth
from pydantic import BaseModel, HttpUrl, Field, field_validator


class ObjectWithId(BaseModel):
    """
    Схема для хранения объекта с id

    Args:
        name (str): название объекта
        id (int): id объекта
    """

    name: str
    id: int

    def as_dict(self):
        return {"name": self.name, "id": self.id}


class BaseManga(BaseModel):
    """
    Схема для хранение базовой версии манги

    Args:
        title (str): название манги
        url (HttpUrl): ссылка на мангу
        poster (HttpUrl): ссылка на постер манги
    """

    title: str
    poster: HttpUrl
    url: HttpUrl

    @property
    def sku(self) -> str:
        """Генерирует sku"""
        if self.title and self.url:
            data = self.title.encode("utf-8")
            return hashlib.sha256(data).hexdigest()[:32]

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "url": str(self.url),
            "poster": str(self.poster),
            "sku": self.sku,
        }


class MangaSchema(BaseManga):
    """
    Схема для хранения версии манги с дополнительными данными (Наследуется от BaseManga)

    Args:
        genres (list[str]): список жанров (строки)
        author (str | None): автор манги
        language (str | None): язык манги
        gallery (list[HttpUrl]): список ссылок на изображения
    """

    genres: list[str] = Field(default_factory=list)
    author: str | None = Field(default=None)
    language: str | None = Field(default=None)

    gallery: list[HttpUrl] = Field(default_factory=list)

    def as_dict(self) -> dict:
        return super().as_dict() | {
            "genres": self.genres,
            "author": self.author,
            "language": self.language,
            "gallery": [str(x) for x in self.gallery],
        }


class OutputMangaSchema(MangaSchema):
    """
    Схема для хранении версии манги из БД

    Args:
        id (int): Внутренний ID либо сайта, либо БД
        pdf_id (int): ID - PDF в ТГ боте
    """

    genres: list[ObjectWithId] = Field(default_factory=list)
    author: ObjectWithId | None = Field(default=None)
    language: ObjectWithId | None = Field(default=None)
    pdf_id: str | None = Field(default=None)

    id: int

    def as_dict(self):
        return super().as_dict() | {
            "id": self.id,
            "genres": [x.as_dict() for x in self.genres],
            "author": self.author.as_dict() if self.author else None,
            "language": self.language.as_dict() if self.language else None,
            "gallery": [str(x) for x in self.gallery],
        }

    def to_manga(self) -> MangaSchema:
        """
        Преобразует OutputMangaSchema в MangaSchema

        Returns:
            MangaSchema: экземпляр MangaSchema
        """
        return MangaSchema(
            title=self.title,
            url=self.url,
            poster=self.poster,
            genres=[x.name for x in self.genres],
            author=self.author.name if self.author else None,
            language=self.language.name if self.language else None,
            gallery=self.gallery,
        )


class ApiOutputManga(OutputMangaSchema):
    """
    Схема для отображения манги в API с добавленным sku
    """

    manga_sku: str | None = Field(default=None, alias="sku", serialization_alias="sku")

    @field_validator("manga_sku", mode="before")
    @classmethod
    def set_sku_if_none(cls, v, info):
        if v is None:
            title = info.data.get("title")
            if title:
                data = title.encode("utf-8")
                return hashlib.sha256(data).hexdigest()[:32]
        return v


class ProxySchema(BaseModel):
    """
    Схема данных для настройки прокси-сервера с аутентификацией

    Args:
        proxy (str): ip адрес сервера
        login (str | None): логин для авторизации
        password (str | None): пароль для авторизации
    """

    proxy: str
    login: str | None = Field(default=None)
    password: str | None = Field(default=None)

    def auth(self):
        raise NotImplementedError("Метод auth должен быть реализован в потомках")

    @classmethod
    def create(cls, proxy: str):
        try:
            proxy, auth = proxy.split("@")
            try:
                login, password = auth.split(":")
                return cls(proxy=proxy, login=login, password=password)
            except ValueError:
                return cls(proxy=proxy, login=auth)

        except ValueError:
            return cls(proxy=proxy)

    def __hash__(self):
        return hash(str(self.proxy))  # или hash(self.proxy)


class AiohttpProxy(ProxySchema):
    def auth(self) -> dict[str, str | BasicAuth]:
        return {
            "proxy": self.proxy,
            "proxy_auth": BasicAuth(login=self.login, password=self.password or "")
            if self.login
            else None,
        }
