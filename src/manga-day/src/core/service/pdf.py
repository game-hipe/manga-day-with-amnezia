import io
import asyncio

from concurrent.futures import ThreadPoolExecutor
from typing import overload, Unpack
from pathlib import Path

import aiohttp

from loguru import logger
from PIL import Image
from PIL.ImageFile import ImageFile

from ..abstract.request import RequestItem
from ..entities.schemas import MangaSchema, OutputMangaSchema
from ..manager.request import RequestManager


class PDFService:
    """
    Класс для преоброзование фоток в PDF

    Основной метод:
        download(gallery, path) - Скачивает фотки, и сохраняет в виде PDF

    NOTE:
        В будущем можно добавить REDIS, для кэширование
    """

    BASE_PATH: str = "."
    BASE_MAX_WORKER: int = 5

    @overload
    def __init__(
        self, session: RequestManager, max_workers: int | None = None
    ) -> None: ...

    @overload
    def __init__(
        self,
        session: aiohttp.ClientSession,
        max_workers: int | None = None,
        **kwargs: Unpack[RequestItem],
    ) -> None: ...

    def __init__(
        self,
        session: RequestManager | aiohttp.ClientSession,
        max_workers: int | None = None,
        **kwargs,
    ) -> None:
        kwargs["maxsize"] = kwargs.get(
            "maxsize", 1
        )  # Число 1 выбрано так-как кэш может "Съесть" всю память

        if isinstance(session, RequestManager):
            self.session = session
        else:
            self.session = RequestManager(session, **kwargs)

        self.executer = ThreadPoolExecutor(
            max_workers=max_workers or self.BASE_MAX_WORKER
        )

    async def download(
        self, gallery: list[str] | MangaSchema | OutputMangaSchema, path: str | Path
    ) -> Path | None:
        """
        Основной метод для скачивания изображений и сохранения в PDF.
        """
        try:
            urls = await self._prepare_gallery(gallery)

            image_bytes_list = await self._fetch_images(urls)
            if not image_bytes_list:
                logger.warning("Не удалось скачать ни одно изображение.")
                return None

            images = await self._process_images(image_bytes_list)

            final_path = self._ensure_pdf_extension(path)
            return await self._save_as_pdf(images, final_path)

        except Exception as e:
            logger.error(f"Ошибка в процессе скачивания или генерации PDF: {e}")
            return None

    async def _prepare_gallery(
        self, gallery: list[str] | MangaSchema | OutputMangaSchema
    ) -> list[str]:
        """Преобразует входные данные в список URL."""
        if isinstance(gallery, MangaSchema) or isinstance(gallery, OutputMangaSchema):
            return [str(img_url) for img_url in gallery.gallery]
        elif isinstance(gallery, list):
            return gallery
        else:
            raise TypeError(f"Неподдерживаемый тип: {type(gallery).__name__}")

    def _ensure_pdf_extension(self, path: str | Path) -> Path:
        """Гарантирует, что путь заканчивается на .pdf."""
        path = Path(path)
        if path.suffix.lower() != ".pdf":
            path = path.with_suffix(".pdf")
        return path

    async def _fetch_images(self, urls: list[str]) -> list[io.BytesIO | None]:
        """Скачивает все изображения асинхронно."""
        tasks = [self._download_image(url, index) for index, url in enumerate(urls)]
        results = []

        for coro in asyncio.as_completed(tasks):
            response, index = await coro
            results.append((response, index))

        sorted_results = sorted(results, key=lambda x: x[1])
        return [res[0] for res in sorted_results]

    async def _process_images(
        self, buffers: list[io.BytesIO | None]
    ) -> list[ImageFile]:
        """Конвертирует байты в объекты PIL.Image в пуле потоков."""
        loop = asyncio.get_running_loop()
        valid_buffers = [buf for buf in buffers if buf is not None]

        if not valid_buffers:
            return []

        images = await loop.run_in_executor(
            self.executer,
            lambda: [self._create_image(buffer) for buffer in valid_buffers],
        )
        return images

    async def _save_as_pdf(self, images: list[ImageFile], path: Path) -> Path | None:
        """Сохраняет изображения в виде PDF."""
        if not images:
            logger.warning("Нет изображений для сохранения в PDF.")
            return None

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.executer, lambda: self._build_pdf(images, path)
        )

    async def _download_image(
        self, url: str, index: int
    ) -> tuple[io.BytesIO | None, int]:
        response = await self.session.get(url, "read")
        if response:
            return io.BytesIO(response), index
        return None, index

    def _create_image(self, buffer: io.BytesIO) -> ImageFile:
        return Image.open(buffer)

    def _build_pdf(self, images: list[ImageFile], path: Path | str) -> Path | None:
        try:
            images[0].save(path, save_all=True, append_images=images[1:])
            return Path(path)
        except Exception as e:
            logger.error(f"Произошла ошибка во время генерации PDF (error={e})")
