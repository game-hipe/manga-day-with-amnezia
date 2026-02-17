import os

from pathlib import Path

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, FSInputFile

from ....core.entities.schemas import OutputMangaSchema
from ....core.service import PDFService
from ....core.manager import MangaManager
from .._text import GREETING, HELP, SHOW_MANGA


class CommandsHandler:
    BASE_SAVE_PATH: str = "var/pdf"

    def __init__(
        self, manager: MangaManager, pdf: PDFService, save_path: str | None = None
    ):
        self.pdf = pdf
        self.manager = manager
        self.save_path = Path(save_path or self.BASE_SAVE_PATH)
        self.router = Router()
        self.register_handlers()

    def register_handlers(self):
        self.router.message.register(self.start, Command("start"))
        self.router.message.register(self.help, Command("help"))
        self.router.message.register(self.download, Command("download"))

    async def start(self, message: Message, command: CommandObject):
        if command.args:
            manga = await self._get_manga(command.args)
            if manga is None:
                await message.answer(
                    f"Не найдена манга по запросу {command.args} (ﾉД`)"
                )
                return

            msg = await message.answer(
                f"Манга {manga.title} Найдена! Пожалуйста подождите..."
            )
            await self.download_manga(manga, msg)
            return

        await message.answer(GREETING)

    async def help(self, message: Message):
        await message.answer(HELP)

    async def download(self, message: Message):
        try:
            command, query = message.text.split()
            manga = await self._get_manga(query)

            if manga is None:
                await message.answer(f"Не найдена манга по запросу {query} (ﾉД`)")
                return

            msg = await message.answer(
                f"Манга {manga.title} Найдена! Пожалуйста подождите..."
            )
            await self.download_manga(manga, msg)

        except ValueError:
            await message.answer(
                "Пожалуйста введите данные в виде <code>/download [АРТИКУЛ или URL]</code>"
            )

    async def _get_manga(self, query: str):
        if query.startswith("http://") or query.startswith("https://"):
            manga = await self.manager.get_manga_by_url(query)
        else:
            manga = await self.manager.get_manga_by_sku(query)

        return manga

    async def download_manga(self, manga: OutputMangaSchema, message: Message):
        file = None
        try:
            if manga.pdf_id:
                await message.answer_document(
                    manga.pdf_id,
                    caption=SHOW_MANGA.format(
                        title=manga.title,
                        genres=", ".join(x.name for x in manga.genres) or "Отсутствует",
                        author=manga.author.name if manga.author else "Неизвестно",
                        language=manga.language.name
                        if manga.language
                        else "Неизвестно",
                        sku=manga.sku,
                    ),
                )
                return

            path = await self.pdf.download(manga, self.save_path / manga.sku)
            if path is None:
                await message.answer(f"Не удалось скачать мангу {manga.title} (ﾉД`)")
                return

            file = FSInputFile(path)
            sent_message = await message.answer_document(
                file,
                caption=SHOW_MANGA.format(
                    title=manga.title,
                    genres=", ".join(x.name for x in manga.genres) or "Отсутствует",
                    author=manga.author.name if manga.author else "Неизвестно",
                    language=manga.language.name if manga.language else "Неизвестно",
                    sku=manga.sku,
                ),
            )

            if sent_message.document:
                file_id = sent_message.document.file_id

            await self.manager.add_pdf(file_id, manga.id)
        except Exception as e:
            await message.answer(
                f"Произошла ошибка при загрузке манги {manga.title} ({e})"
            )
        finally:
            await message.delete()
            if file:
                os.remove(file.path)
