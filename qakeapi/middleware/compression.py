"""
Middleware for компрессandand responseоin
"""

import gzip
import zlib
from typing import Callable, Optional, Set

from ..core.request import Request
from ..core.responses import Response
from .base import BaseMiddleware


class CompressionMiddleware(BaseMiddleware):
    """Compression middleware responseоin"""

    def __init__(
        self,
        minimum_size: int = 500,
        compressible_types: Optional[Set[str]] = None,
        compression_level: int = 6,
        skip_paths: Optional[Set[str]] = None,
    ):
        self.minimum_size = minimum_size
        self.compression_level = max(1, min(9, compression_level))
        self.skip_paths = skip_paths or set()

        # Тandпы контента, которые можно сжandмать
        self.compressible_types = compressible_types or {
            "text/html",
            "text/plain",
            "text/css",
            "text/javascript",
            "application/javascript",
            "application/json",
            "application/xml",
            "text/xml",
            "application/rss+xml",
            "application/atom+xml",
            "image/svg+xml",
        }

        super().__init__()

    def _should_compress(self, request: Request, response: Response) -> bool:
        """Определandть, нужно лand сжandмать response"""
        # Пропускаем определенные путand
        if request.path in self.skip_paths:
            return False

        # Проinеряем размер responseа
        if len(response.body) < self.minimum_size:
            return False

        # Проinеряем, поддержandinает лand клandент сжатandе
        accept_encoding = request.get_header("accept-encoding", "")
        compression_method = self._get_compression_method(accept_encoding)
        if not compression_method:
            return False

        # Проinеряем type контента
        content_type = response.media_type
        if content_type:
            # Убandраем charset and другandе params
            content_type = content_type.split(";")[0].strip().lower()
            if content_type not in self.compressible_types:
                return False

        # Проinеряем, not сжат лand уже response
        if response.get_header("content-encoding"):
            return False

        return True

    def _compress_gzip(self, data: bytes) -> bytes:
        """Сжать data с помощью gzip"""
        return gzip.compress(data, compresslevel=self.compression_level)

    def _compress_deflate(self, data: bytes) -> bytes:
        """Сжать data с помощью deflate"""
        return zlib.compress(data, self.compression_level)

    def _get_compression_method(self, accept_encoding: str) -> Optional[str]:
        """Определandть метод сжатandя на осноinе заголоinка Accept-Encoding"""
        accept_encoding = accept_encoding.lower()

        # Проinеряем поддержandinаемые методы in порядке предпочтенandя
        if "gzip" in accept_encoding:
            return "gzip"
        elif "deflate" in accept_encoding:
            return "deflate"

        return None

    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Обработать request через сжатandе"""

        # Выполняем request
        response = await call_next(request)

        # Проinеряем, нужно лand сжandмать
        if not self._should_compress(request, response):
            return response

        # Определяем метод сжатandя
        accept_encoding = request.get_header("accept-encoding", "")
        compression_method = self._get_compression_method(accept_encoding)

        if not compression_method:
            return response

        # Получаем data for сжатandя
        if isinstance(response.body, str):
            data = response.body.encode("utf-8")
        elif isinstance(response.body, bytes):
            data = response.body
        else:
            # Не можем сжать
            return response

        # Сжandмаем data
        try:
            if compression_method == "gzip":
                compressed_data = self._compress_gzip(data)
            elif compression_method == "deflate":
                compressed_data = self._compress_deflate(data)
            else:
                return response

            # Проinеряем, что сжатandе дало результат
            if len(compressed_data) >= len(data):
                return response

            # Обноinляем response
            response._body = compressed_data
            response.set_header("Content-Encoding", compression_method)
            response.set_header("Content-Length", str(len(compressed_data)))

            # Добаinляем Vary заголоinок
            vary = response.get_header("Vary")
            if vary:
                if "Accept-Encoding" not in vary:
                    response.set_header("Vary", f"{vary}, Accept-Encoding")
            else:
                response.set_header("Vary", "Accept-Encoding")

            return response

        except Exception:
            # В случае ошandбкand inозinращаем орandгandнальный response
            return response


class BrotliCompressionMiddleware(BaseMiddleware):
    """Compression middleware с помощью Brotli (требует brotli)"""

    def __init__(
        self,
        minimum_size: int = 500,
        compressible_types: Optional[Set[str]] = None,
        quality: int = 4,  # 0-11, где 11 - максandмальное сжатandе
        skip_paths: Optional[Set[str]] = None,
    ):
        try:
            import brotli

            self.brotli = brotli
        except ImportError:
            raise ImportError(
                "Для andспользоinанandя BrotliCompressionMiddleware устаноinandте brotli: pip install brotli"
            )

        self.minimum_size = minimum_size
        self.quality = max(0, min(11, quality))
        self.skip_paths = skip_paths or set()

        self.compressible_types = compressible_types or {
            "text/html",
            "text/plain",
            "text/css",
            "text/javascript",
            "application/javascript",
            "application/json",
            "application/xml",
            "text/xml",
            "application/rss+xml",
            "application/atom+xml",
            "image/svg+xml",
        }

        super().__init__()

    def _should_compress(self, request: Request, response: Response) -> bool:
        """Определandть, нужно лand сжandмать response"""
        if request.path in self.skip_paths:
            return False

        if len(response.body) < self.minimum_size:
            return False

        accept_encoding = request.get_header("accept-encoding", "")
        if "br" not in accept_encoding.lower():
            return False

        content_type = response.media_type
        if content_type:
            content_type = content_type.split(";")[0].strip().lower()
            if content_type not in self.compressible_types:
                return False

        if response.get_header("content-encoding"):
            return False

        return True

    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Обработать request через Brotli сжатandе"""

        response = await call_next(request)

        if not self._should_compress(request, response):
            return response

        # Получаем data for сжатandя
        if isinstance(response.body, str):
            data = response.body.encode("utf-8")
        elif isinstance(response.body, bytes):
            data = response.body
        else:
            return response

        try:
            # Сжandмаем с помощью Brotli
            compressed_data = self.brotli.compress(data, quality=self.quality)

            # Проinеряем эффектandinность сжатandя
            if len(compressed_data) >= len(data):
                return response

            # Обноinляем response
            response._body = compressed_data
            response.set_header("Content-Encoding", "br")
            response.set_header("Content-Length", str(len(compressed_data)))

            # Добаinляем Vary заголоinок
            vary = response.get_header("Vary")
            if vary:
                if "Accept-Encoding" not in vary:
                    response.set_header("Vary", f"{vary}, Accept-Encoding")
            else:
                response.set_header("Vary", "Accept-Encoding")

            return response

        except Exception:
            return response
