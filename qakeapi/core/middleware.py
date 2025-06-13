import time
from typing import Any, Callable, Dict, List, Optional, Type

from .requests import Request
from .responses import JSONResponse, Response


class Middleware:
    async def __call__(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        return await call_next(request)


class CORSMiddleware(Middleware):
    def __init__(
        self,
        allow_origins: List[str] = ["*"],
        allow_methods: List[str] = ["GET"],
        allow_headers: List[str] = [],
        allow_credentials: bool = False,
        expose_headers: List[str] = [],
        max_age: int = 600,
    ):
        self.allow_origins = allow_origins
        self.allow_methods = allow_methods
        self.allow_headers = allow_headers
        self.allow_credentials = allow_credentials
        self.expose_headers = expose_headers
        self.max_age = max_age

    async def __call__(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        if request.method == "OPTIONS":
            response = Response()
        else:
            response = await call_next(request)

        origin = request.headers.get(b"origin", b"").decode()

        if origin:
            if "*" in self.allow_origins:
                response.headers["Access-Control-Allow-Origin"] = "*"
            elif origin in self.allow_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Vary"] = "Origin"

            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"

            if self.expose_headers:
                response.headers["Access-Control-Expose-Headers"] = ", ".join(
                    self.expose_headers
                )

            if request.method == "OPTIONS":
                response.headers["Access-Control-Allow-Methods"] = ", ".join(
                    self.allow_methods
                )
                response.headers["Access-Control-Allow-Headers"] = ", ".join(
                    self.allow_headers
                )
                response.headers["Access-Control-Max-Age"] = str(self.max_age)

        return response


class RequestLoggingMiddleware(Middleware):
    async def __call__(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        print(
            f"{request.method} {request.path} "
            f"- {response.status_code} "
            f"- {duration:.3f}s"
        )

        return response


class ErrorHandlingMiddleware(Middleware):
    async def __call__(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            return JSONResponse(
                {"detail": str(exc), "type": exc.__class__.__name__}, status_code=500
            )


class AuthenticationMiddleware(Middleware):
    def __init__(
        self,
        auth_header: str = "Authorization",
        auth_scheme: str = "Bearer",
        exempt_paths: List[str] = [],
    ):
        self.auth_header = auth_header
        self.auth_scheme = auth_scheme
        self.exempt_paths = exempt_paths

    async def __call__(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        if request.path in self.exempt_paths:
            return await call_next(request)

        auth_header = request.headers.get(
            self.auth_header.lower().encode(), b""
        ).decode()

        if not auth_header:
            return JSONResponse({"detail": "Not authenticated"}, status_code=401)

        scheme, token = auth_header.split(" ", 1)

        if scheme.lower() != self.auth_scheme.lower():
            return JSONResponse(
                {
                    "detail": f"Invalid authentication scheme. Expected {self.auth_scheme}"
                },
                status_code=401,
            )

        request.auth_token = token
        return await call_next(request)


class RateLimitMiddleware(Middleware):
    def __init__(self, requests_per_minute: int = 60, window_size: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_size = window_size
        self.requests: Dict[str, List[float]] = {}

    def _clean_old_requests(self, client: str):
        """Remove requests older than window_size"""
        current_time = time.time()
        self.requests[client] = [
            req_time
            for req_time in self.requests[client]
            if current_time - req_time < self.window_size
        ]

    async def __call__(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        client = request.client()[0] or "unknown"

        if client not in self.requests:
            self.requests[client] = []

        self._clean_old_requests(client)

        if len(self.requests[client]) >= self.requests_per_minute:
            return JSONResponse({"detail": "Too many requests"}, status_code=429)

        self.requests[client].append(time.time())
        return await call_next(request)
