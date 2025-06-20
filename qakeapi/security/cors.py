from typing import List, Optional, Callable
from ..core.requests import Request
from ..core.responses import Response

class CORSMiddleware:
    def __init__(
        self,
        allow_origins: List[str] = ["*"],
        allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers: List[str] = ["*"],
        allow_credentials: bool = False,
        max_age: int = 600,
    ):
        self.allow_origins = allow_origins
        self.allow_methods = allow_methods
        self.allow_headers = allow_headers
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    async def __call__(self, request: Request, handler: Callable) -> Response:
        if request.method == "OPTIONS":
            return self._handle_preflight(request)
        
        response = await handler(request)
        return self._add_cors_headers(response, request.headers.get(b"origin", b"").decode())

    def _handle_preflight(self, request: Request) -> Response:
        origin = request.headers.get(b"origin", b"").decode()
        
        if not self._is_origin_allowed(origin):
            return Response.json({"detail": "Origin not allowed"}, status_code=403)

        response = Response.json({})
        response.headers.extend([
            (b"access-control-allow-origin", origin.encode() if origin != "*" else b"*"),
            (b"access-control-allow-methods", ", ".join(self.allow_methods).encode()),
            (b"access-control-allow-headers", ", ".join(self.allow_headers).encode()),
            (b"access-control-max-age", str(self.max_age).encode()),
        ])

        if self.allow_credentials:
            response.headers.append((b"access-control-allow-credentials", b"true"))

        return response

    def _add_cors_headers(self, response: Response, origin: str) -> Response:
        if self._is_origin_allowed(origin):
            response.headers.append(
                (b"access-control-allow-origin", origin.encode() if origin != "*" else b"*")
            )
            if self.allow_credentials:
                response.headers.append((b"access-control-allow-credentials", b"true"))
        return response

    def _is_origin_allowed(self, origin: str) -> bool:
        return "*" in self.allow_origins or origin in self.allow_origins 