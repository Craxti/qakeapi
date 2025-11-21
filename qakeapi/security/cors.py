"""
CORS (Cross-Origin Resource Sharing) middleware.

This module provides CORS middleware for handling cross-origin requests.
"""

from typing import Any, Dict, List, Optional

from qakeapi.core.middleware import BaseMiddleware


class CORSMiddleware(BaseMiddleware):
    """
    CORS middleware for handling cross-origin requests.
    """

    def __init__(
        self,
        app: Any = None,
        allow_origins: Optional[List[str]] = None,
        allow_methods: Optional[List[str]] = None,
        allow_headers: Optional[List[str]] = None,
        allow_credentials: bool = False,
        expose_headers: Optional[List[str]] = None,
        max_age: int = 600,
    ):
        """
        Initialize CORS middleware.

        Args:
            app: ASGI application
            allow_origins: List of allowed origins (use ["*"] for all)
            allow_methods: List of allowed HTTP methods
            allow_headers: List of allowed headers
            allow_credentials: Whether to allow credentials
            expose_headers: List of headers to expose
            max_age: Preflight cache max age in seconds
        """
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or [
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "PATCH",
            "OPTIONS",
        ]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.expose_headers = expose_headers or []
        self.max_age = max_age

    def _is_origin_allowed(self, origin: str) -> bool:
        """
        Check if origin is allowed.

        Args:
            origin: Origin header value

        Returns:
            True if allowed
        """
        if "*" in self.allow_origins:
            return True
        return origin in self.allow_origins

    async def process_http(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """
        Process HTTP request with CORS.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Get origin from headers
        headers = dict(scope.get("headers", []))
        origin = None
        for key, value in headers.items():
            if key.lower() == b"origin":
                origin = value.decode()
                break

        # Handle preflight request
        if scope.get("method") == "OPTIONS":
            await self._handle_preflight(scope, send, origin)
            return

        # Process request
        async def send_wrapper(message: Dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                # Add CORS headers
                cors_headers = self._get_cors_headers(origin)
                existing_headers = message.get("headers", [])
                message["headers"] = existing_headers + cors_headers

            await send(message)

        if self.app:
            await self.app(scope, receive, send_wrapper)

    async def _handle_preflight(
        self, scope: Dict[str, Any], send: Any, origin: Optional[str]
    ) -> None:
        """
        Handle preflight OPTIONS request.

        Args:
            scope: ASGI scope
            send: ASGI send callable
            origin: Origin header value
        """
        # Get request method and headers
        headers = dict(scope.get("headers", []))
        request_method = None
        request_headers = None

        for key, value in headers.items():
            if key.lower() == b"access-control-request-method":
                request_method = value.decode()
            elif key.lower() == b"access-control-request-headers":
                request_headers = value.decode()

        # Build CORS headers
        cors_headers = []

        if origin and self._is_origin_allowed(origin):
            cors_headers.append([b"access-control-allow-origin", origin.encode()])

            if self.allow_credentials:
                cors_headers.append([b"access-control-allow-credentials", b"true"])

            if request_method:
                methods = ", ".join(self.allow_methods)
                cors_headers.append([b"access-control-allow-methods", methods.encode()])

            if request_headers:
                if "*" in self.allow_headers:
                    headers_str = request_headers
                else:
                    headers_str = ", ".join(self.allow_headers)
                cors_headers.append(
                    [b"access-control-allow-headers", headers_str.encode()]
                )

            if self.max_age > 0:
                cors_headers.append(
                    [b"access-control-max-age", str(self.max_age).encode()]
                )

        # Send response
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": cors_headers,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"",
            }
        )

    def _get_cors_headers(self, origin: Optional[str]) -> List[List[bytes]]:
        """
        Get CORS headers for response.

        Args:
            origin: Origin header value

        Returns:
            List of CORS headers
        """
        headers = []

        if origin and self._is_origin_allowed(origin):
            headers.append([b"access-control-allow-origin", origin.encode()])

            if self.allow_credentials:
                headers.append([b"access-control-allow-credentials", b"true"])

            if self.expose_headers:
                headers.append(
                    [
                        b"access-control-expose-headers",
                        ", ".join(self.expose_headers).encode(),
                    ]
                )

        return headers
