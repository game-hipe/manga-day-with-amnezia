import hashlib

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, JSON, Index


class Base(DeclarativeBase): ...


class Genre(Base):
    """
    Модель жанра

    Args:
        id (int): id жанра
        name (str): название жанра
    """

    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    mangas_connection: Mapped[list["GenreManga"]] = relationship(
        "GenreManga", back_populates="genre"
    )


class Author(Base):
    """
    Модель автора

    Args:
        id (int): id автора
        name (str): имя автора

        mangas (list[Manga]): список манги
    """

    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    mangas: Mapped[list["Manga"]] = relationship("Manga", back_populates="author")


class Language(Base):
    """
    Модель языка

    Args:
        id (int): id языка
        name (str): название языка

        mangas (list[Manga]): список манги
    """

    __tablename__ = "language"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    mangas: Mapped[list["Manga"]] = relationship("Manga", back_populates="language")


class GenreManga(Base):
    """
    Модель связи манги с жанрами

    Args:
        id (int): id связи
        genre_id (int): id жанра
        manga_id (int): id манги

        genre (Genre): жанр
        manga (Manga): манга
    """

    __tablename__ = "genre_manga"

    id: Mapped[int] = mapped_column(primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id"))
    manga_id: Mapped[int] = mapped_column(ForeignKey("mangas.id"))

    genre: Mapped["Genre"] = relationship("Genre", back_populates="mangas_connection")
    manga: Mapped["Manga"] = relationship("Manga", back_populates="genres_connection")


class Gallery(Base):
    """
    Модель галереи

    Args:
        id (int): id галереи
        urls (list[str]): список ссылок на изображения
        manga_id (int): id манги
    """

    __tablename__ = "gallery"
    id: Mapped[int] = mapped_column(primary_key=True)
    urls: Mapped[list[str]] = mapped_column(JSON())
    manga_id: Mapped[int] = mapped_column(ForeignKey("mangas.id"))

    manga: Mapped["Manga"] = relationship("Manga", back_populates="gallery")


class GeneratedPdf(Base):
    """
    Модель сгенерированного pdf

    Args:
        id_manga (int): ID - на мангу
        id_file (int): ID файла в тг
    """

    __tablename__ = "generated_pdf"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_manga: Mapped[int] = mapped_column(ForeignKey("mangas.id"), unique=True)
    id_file: Mapped[str] = mapped_column(String(256))
    __table_args__ = (Index("idx_generated_pdf_id_file", "id_file"),)

    manga: Mapped["Manga"] = relationship("Manga", back_populates="generated_pdf")


class Manga(Base):
    """
    Модель манги

    Args:
        id (int): id манги
        title (str): название манги
        url (str): ссылка на мангу
        poster (str): ссылка на постер манги
        language_id (int): id языка
        author_id (int): id автора
        sku (str): уникальный идентификатор манги
        genres_connection (list[GenreManga]): список связей с жанрами
        author (Author): автор манги
        language (Language): язык манги
        gallery (list[Gallery]): список ссылок на изображения
        genres (list[Genre]): список жанров манги

    """

    __tablename__ = "mangas"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(1024))
    url: Mapped[str] = mapped_column(String(2048))
    poster: Mapped[str] = mapped_column(String(2048))

    language_id: Mapped[int] = mapped_column(ForeignKey("language.id"), nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"), nullable=True)
    sku: Mapped[str] = mapped_column(String(32), unique=True, index=True)

    genres_connection: Mapped[list["GenreManga"]] = relationship(
        "GenreManga", back_populates="manga"
    )

    author: Mapped["Author"] = relationship("Author", back_populates="mangas")

    language: Mapped["Language"] = relationship("Language", back_populates="mangas")

    gallery: Mapped["Gallery"] = relationship("Gallery", back_populates="manga")

    generated_pdf: Mapped["GeneratedPdf"] = relationship(
        "GeneratedPdf", back_populates="manga"
    )

    @property
    def genres(self) -> list["Genre"]:
        return [genre.genre for genre in self.genres_connection]

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "poster": self.poster,
            "genres": self.genres,
            "author": self.author.name,
            "language": self.language.name,
            "gallery": self.gallery.urls,
        }

    def __init__(self, **kw):
        """Инициализирует экземпляр модели.

        Вызывает родительский конструктор и при необходимости генерирует SKU
        на основе заголовка и URL, если SKU ещё не установлен.

        Args:
            **kw: Аргументы для инициализации полей модели.
        """
        super().__init__(**kw)
        if self.title and self.url and not self.sku:
            self.generate_sku()

    def generate_sku(self):
        """Генерирует и устанавливает уникальный идентификатор (SKU) на основе заголовка.

        Использует SHA-256 хэш от названия манги (в кодировке UTF-8),
        обрезает до 32 символов и присваивает полю `sku`.

        Raises:
            AttributeError: Если `title` равен None.
        """
        if self.title and self.url:
            data = self.title.encode("utf-8")
            self.sku = hashlib.sha256(data).hexdigest()[:32]

    __table_args__ = (
        Index("idx_sku", "sku"),
        Index("idx_title", "title"),
        Index("idx_url", "url"),
    )
