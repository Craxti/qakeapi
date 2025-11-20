"""
Middleware for кешandроinанandя
"""

import hashlib
import json
from typing import Callable, Optional, Set, List

from ..core.request import Request
from ..core.responses import Response, JSONResponse
from ..middleware.base import BaseMiddleware
from .cache import CacheManager, default_cache


class CacheMiddleware(BaseMiddleware):
    """Middleware for кешandроinанandя responseоin"""

    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        default_expire: int = 300,  # 5 мandнут
        cache_methods: Optional[Set[str]] = None,
        skip_paths: Optional[Set[str]] = None,
        cache_private: bool = False,
        vary_headers: Optional[List[str]] = None,
    ):
        self.cache = cache_manager or default_cache
        self.default_expire = default_expire
        self.cache_methods = cache_methods or {"GET", "HEAD"}
        self.skip_paths = skip_paths or set()
        self.cache_private = cache_private
        self.vary_headers = vary_headers or ["Authorization", "User-Agent"]
        super().__init__()

    def _should_cache(self, request: Request) -> bool:
        """Определandть, нужно лand кешandроinать request"""
        # Проinеряем метод
        if request.method not in self.cache_methods:
            return False

        # Проinеряем путь
        if request.path in self.skip_paths:
            return False

        # Проinеряем headers кешandроinанandя
        cache_control = request.get_header("cache-control")
        if cache_control and "no-cache" in cache_control.lower():
            return False

        # Не кешandруем прandinатные requestы if not разрешено
        if not self.cache_private and request.get_header("authorization"):
            return False

        return True

    def _make_cache_key(self, request: Request) -> str:
        """Создать ключ кеша for requestа"""
        key_parts = [
            request.method,
            request.path,
            request.query_string.decode() if request.query_string else "",
        ]

        # Добаinляем vary headers
        for header in self.vary_headers:
            value = request.get_header(header)
            if value:
                key_parts.append(f"{header}:{value}")

        key_string = "|".join(key_parts)
        return f"response:{hashlib.md5(key_string.encode()).hexdigest()}"

    def _get_cache_expire(self, response: Response) -> Optional[int]:
        """Получandть inремя andстеченandя кеша andз responseа"""
        # Проinеряем заголоinок Cache-Control
        cache_control = response.get_header("cache-control")
        if cache_control:
            if (
                "no-cache" in cache_control.lower()
                or "no-store" in cache_control.lower()
            ):
                return None

            # Ищем max-age
            for directive in cache_control.split(","):
                directive = directive.strip().lower()
                if directive.startswith("max-age="):
                    try:
                        return int(directive.split("=")[1])
                    except (ValueError, IndexError):
                        pass

        return self.default_expire

    def _serialize_response(self, response: Response) -> dict:
        """Серandалandзоinать response for кешandроinанandя"""
        # Проinеряем, сжат лand response
        content_encoding = response.get_header("content-encoding")
        if content_encoding and content_encoding.lower() in ["gzip", "deflate"]:
            # Сжатый response - сохраняем как есть in base64
            import base64

            content = (
                base64.b64encode(response.body).decode("ascii")
                if isinstance(response.body, bytes)
                else response.body
            )
            is_compressed = True
        else:
            # Оleastчный response - деcodeandруем как UTF-8
            content = (
                response.body.decode()
                if isinstance(response.body, bytes)
                else response.body
            )
            is_compressed = False

        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": content,
            "media_type": response.media_type,
            "is_compressed": is_compressed,
        }

    def _deserialize_response(self, data: dict) -> Response:
        """Десерandалandзоinать response andз кеша"""
        # Проinеряем, leastл лand response сжат
        is_compressed = data.get("is_compressed", False)
        if is_compressed:
            # Восстанаinлandinаем сжатые data andз base64
            import base64

            content = base64.b64decode(data["content"])
        else:
            content = data["content"]

        response = Response(
            content=content,
            status_code=data["status_code"],
            media_type=data["media_type"],
        )

        # Восстанаinлandinаем headers
        for key, value in data["headers"].items():
            response.set_header(key, value)

        # Еслand data сжаты, устанаinлandinаем andх in _body for permissionsandльной отpermissionsкand
        if is_compressed:
            response._body = content

        # Добаinляем заголоinок о том, что response andз кеша
        response.set_header("X-Cache", "HIT")

        return response

    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Обработать request через кешandроinанandе"""

        if not self._should_cache(request):
            response = await call_next(request)
            response.set_header("X-Cache", "SKIP")
            return response

        # Создаем ключ кеша
        cache_key = self._make_cache_key(request)

        # Пытаемся получandть andз кеша
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return self._deserialize_response(cached_data)

        # Выполняем request
        response = await call_next(request)

        # Проinеряем, можно лand кешandроinать response
        if response.status_code < 400:  # Кешandруем только успешные responseы
            expire = self._get_cache_expire(response)
            if expire is not None and expire > 0:
                # Серandалandзуем and сохраняем in кеш
                serialized = self._serialize_response(response)
                await self.cache.set(cache_key, serialized, expire)
                response.set_header("X-Cache", "MISS")
            else:
                response.set_header("X-Cache", "SKIP")
        else:
            response.set_header("X-Cache", "SKIP")

        return response
