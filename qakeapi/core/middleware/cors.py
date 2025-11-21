import logging
from typing import Dict, List, Optional

from ..requests import Request
from ..responses import Response

logger = logging.getLogger(__name__)


class CORSConfig:
    """Configuration for CORS middleware"""

    def __init__(
        self,
        allow_origins: List[str] = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        allow_credentials: bool = False,
        expose_headers: List[str] = None,
        max_age: int = 600,
    ):
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or [
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "OPTIONS",
            "PATCH",
        ]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.expose_headers = expose_headers or []
        self.max_age = max_age


class CORSMiddleware:
    """Middleware for handling CORS"""

    def __init__(self, config: CORSConfig = None):
        self.config = config or CORSConfig()

    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed"""
        if "*" in self.config.allow_origins:
            return True
        return origin in self.config.allow_origins

    def _get_allow_headers(self, request_headers: str = None) -> str:
        """Get allowed headers"""
        if "*" in self.config.allow_headers:
            return request_headers if request_headers else "*"
        return ", ".join(self.config.allow_headers)

    def _get_origin_from_headers(self, headers) -> Optional[str]:
        """Extract origin from headers"""
        # Headers может быть словарем или списком кортежей
        if isinstance(headers, dict):
            # Проверяем разные варианты ключей
            for key in [b"origin", "origin", "Origin", b"Origin"]:
                if key in headers:
                    origin = headers[key]
                    return origin.decode() if isinstance(origin, bytes) else str(origin)
            # Попробуем найти в нижнем регистре (для словарей с ключами в нижнем регистре)
            if "origin" in headers:
                origin = headers["origin"]
                return origin.decode() if isinstance(origin, bytes) else str(origin)
            # Ищем по всем ключам
            for key, value in headers.items():
                key_str = key.decode().lower() if isinstance(key, bytes) else key.lower() if isinstance(key, str) else str(key).lower()
                if key_str == "origin":
                    return value.decode() if isinstance(value, bytes) else str(value)
        elif isinstance(headers, list):
            # Ищем в списке кортежей
            for header_name, header_value in headers:
                if isinstance(header_name, bytes):
                    if header_name.lower() == b"origin":
                        return header_value.decode() if isinstance(header_value, bytes) else str(header_value)
                elif isinstance(header_name, str) and header_name.lower() == "origin":
                    return header_value.decode() if isinstance(header_value, bytes) else str(header_value)
        return None

    def _build_preflight_response(self, request: Request) -> Response:
        """Build response for preflight request"""
        origin = self._get_origin_from_headers(request.headers)
        logger.debug(f"Building preflight response for origin: {origin}")

        if not origin:
            return Response(content={"detail": "No origin header"}, status_code=400)

        if not self._is_origin_allowed(origin):
            return Response(content={"detail": "Origin not allowed"}, status_code=400)

        response = Response(content={}, status_code=200)
        
        # Получаем запрошенные заголовки
        requested_headers = request.get_header("access-control-request-headers", "")
        allowed_headers = self._get_allow_headers(requested_headers)
        
        response.headers = [
            (b"Access-Control-Allow-Origin", origin.encode()),
            (
                b"Access-Control-Allow-Methods",
                ", ".join(self.config.allow_methods).encode(),
            ),
            (b"Access-Control-Max-Age", str(self.config.max_age).encode()),
            (
                b"Access-Control-Allow-Headers",
                allowed_headers.encode() if isinstance(allowed_headers, str) else allowed_headers,
            ),
        ]

        if self.config.allow_credentials:
            response.headers.append((b"Access-Control-Allow-Credentials", b"true"))

        if self.config.expose_headers:
            response.headers.append(
                (
                    b"Access-Control-Expose-Headers",
                    ", ".join(self.config.expose_headers).encode(),
                )
            )

        logger.debug(f"Preflight response headers: {response.headers}")
        return response

    def _add_cors_headers(self, response: Response, origin: str) -> None:
        """Add CORS headers to response"""
        if not hasattr(response, "headers"):
            response.headers = {}

        if isinstance(response.headers, dict):
            response.headers = []

        if origin and self._is_origin_allowed(origin):
            response.headers.append((b"Access-Control-Allow-Origin", origin.encode()))

            if self.config.allow_credentials:
                response.headers.append((b"Access-Control-Allow-Credentials", b"true"))

            if self.config.expose_headers:
                response.headers.append(
                    (
                        b"Access-Control-Expose-Headers",
                        ", ".join(self.config.expose_headers).encode(),
                    )
                )

        logger.debug(f"Added CORS headers: {response.headers}")

    async def __call__(self, request: Request, handler) -> Response:
        """Process the request"""
        origin = self._get_origin_from_headers(request.headers)
        logger.debug(
            f"Processing request: {request.method} {request.path} origin: {origin}"
        )

        # Handle preflight requests
        if request.method == "OPTIONS":
            logger.debug("Handling preflight request")
            return self._build_preflight_response(request)

        response = await handler(request)

        # Add CORS headers to response if origin is present and allowed
        if origin and self._is_origin_allowed(origin):
            logger.debug(f"Adding CORS headers for origin: {origin}")
            self._add_cors_headers(response, origin)

        return response
