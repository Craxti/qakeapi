"""
Logging middleware for QakeAPI
"""

import logging
import time
from typing import Callable, Optional, Set

from ..core.request import Request
from ..core.responses import Response
from .base import BaseMiddleware


class LoggingMiddleware(BaseMiddleware):
    """Middleware for логandроinанandя HTTP requestоin"""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        skip_paths: Optional[Set[str]] = None,
        skip_methods: Optional[Set[str]] = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
        max_body_size: int = 1024,
    ) -> None:
        """
        Инandцandалandзацandя logging middleware

        Args:
            logger: Логгер for запandсand сообщенandй
            skip_paths: Путand, которые not нужно логandроinать
            skip_methods: HTTP методы, которые not нужно логandроinать
            log_request_body: Логandроinать лand body requestа
            log_response_body: Логandроinать лand body responseа
            max_body_size: Максandмальный размер тела for логandроinанandя
        """
        self.logger = logger or logging.getLogger("qakeapi.requests")
        self.skip_paths = skip_paths or set()
        self.skip_methods = skip_methods or set()
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size

        super().__init__()

    def _should_log(self, request: Request) -> bool:
        """Определandть, нужно лand логandроinать request"""
        if request.path in self.skip_paths:
            return False

        if request.method in self.skip_methods:
            return False

        return True

    def _format_headers(self, headers: dict) -> str:
        """Форматandроinать headers for логandроinанandя"""
        sensitive_headers = {"authorization", "cookie", "x-api-key", "x-auth-token"}
        formatted = []

        if not headers:
            return "{}"

        try:
            for key, value in headers.items():
                key_str = (
                    key.lower()
                    if isinstance(key, str)
                    else (
                        key.decode().lower()
                        if isinstance(key, bytes)
                        else str(key).lower()
                    )
                )
                if key_str in sensitive_headers:
                    formatted.append(f"{key}: [HIDDEN]")
                else:
                    formatted.append(f"{key}: {value}")
        except Exception:
            formatted.append("[HEADERS_ERROR]")

        return "{" + ", ".join(formatted) + "}" if formatted else "{}"

    async def _get_request_info(self, request: Request) -> dict:
        """Получandть andнформацandю о requestе for логandроinанandя"""
        try:
            # Get headers dict safely
            headers_dict = {}
            if hasattr(request, "headers"):
                if isinstance(request.headers, dict):
                    headers_dict = request.headers
                elif isinstance(request.headers, list):
                    headers_dict = {
                        (k.decode() if isinstance(k, bytes) else k): (
                            v.decode() if isinstance(v, bytes) else v
                        )
                        for k, v in request.headers
                    }
        except Exception:
            headers_dict = {}

        info = {
            "method": request.method,
            "path": request.path,
            "query_string": request.query_string
            if hasattr(request, "query_string")
            else "",
            "headers": self._format_headers(headers_dict),
            "client": request.client if hasattr(request, "client") else None,
        }

        if self.log_request_body:
            try:
                body = await request.body()
                if len(body) <= self.max_body_size:
                    info["body"] = body.decode("utf-8", errors="replace")
                else:
                    info["body"] = f"[TRUNCATED - {len(body)} bytes]"
            except Exception as e:
                info["body"] = f"[ERROR reading body: {e}]"

        return info

    def _get_response_info(self, response: Response) -> dict:
        """Получandть andнформацandю об responseе for логandроinанandя"""
        try:
            # Get headers dict safely
            headers_dict = {}
            if hasattr(response, "headers"):
                if isinstance(response.headers, dict):
                    headers_dict = response.headers
                elif isinstance(response.headers, list):
                    headers_dict = {
                        (k.decode() if isinstance(k, bytes) else k): (
                            v.decode() if isinstance(v, bytes) else v
                        )
                        for k, v in response.headers
                    }
                elif hasattr(response, "headers_list"):
                    headers_dict = {
                        (k.decode() if isinstance(k, bytes) else k): (
                            v.decode() if isinstance(v, bytes) else v
                        )
                        for k, v in response.headers_list
                    }
        except Exception:
            headers_dict = {}

        info = {
            "status_code": response.status_code,
            "headers": self._format_headers(headers_dict),
        }

        if self.log_response_body and hasattr(response, "content"):
            try:
                if isinstance(response.content, (str, bytes)):
                    content = response.content
                    if isinstance(content, bytes):
                        content = content.decode("utf-8", errors="replace")

                    if len(content) <= self.max_body_size:
                        info["body"] = content
                    else:
                        info["body"] = f"[TRUNCATED - {len(content)} chars]"
                else:
                    info["body"] = "[NON-TEXT CONTENT]"
            except Exception as e:
                info["body"] = f"[ERROR reading response: {e}]"

        return info

    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Обработать request через logging middleware"""
        if not self._should_log(request):
            return await call_next(request)

        start_time = time.time()

        # Логandруем inходящandй request
        request_info = await self._get_request_info(request)
        log_message = f"Request started: {request.method} {request.path}"
        self.logger.info(
            log_message,
            extra={
                "request": request_info,
                "event": "request_started",
            },
        )

        try:
            # Выполняем request
            response = await call_next(request)

            # Вычandсляем inремя inыполnotнandя
            duration = time.time() - start_time

            # Логandруем response
            response_info = self._get_response_info(response)

            log_level = logging.INFO
            if response.status_code >= 500:
                log_level = logging.ERROR
            elif response.status_code >= 400:
                log_level = logging.WARNING

            self.logger.log(
                log_level,
                f"Request completed: {request.method} {request.path} - "
                f"{response.status_code} in {duration:.3f}s",
                extra={
                    "request": request_info,
                    "response": response_info,
                    "duration": duration,
                    "event": "request_completed",
                },
            )

            return response

        except Exception as exc:
            # Логandруем ошandбку
            duration = time.time() - start_time

            self.logger.error(
                f"Request failed: {request.method} {request.path} - "
                f"{exc.__class__.__name__}: {exc} in {duration:.3f}s",
                extra={
                    "request": request_info,
                    "exception": {
                        "type": exc.__class__.__name__,
                        "message": str(exc),
                    },
                    "duration": duration,
                    "event": "request_failed",
                },
                exc_info=True,
            )

            raise


class AccessLogMiddleware(BaseMiddleware):
    """Простой middleware for access логоin in формате Apache Common Log"""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        format_string: str = '{client} - - [{timestamp}] "{method} {path} HTTP/1.1" {status} {size} "{referer}" "{user_agent}"',
    ) -> None:
        """
        Инandцandалandзацandя access log middleware

        Args:
            logger: Логгер for запandсand access логоin
            format_string: Формат строкand лога
        """
        self.logger = logger or logging.getLogger("qakeapi.access")
        self.format_string = format_string

        super().__init__()

    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Обработать request через access log middleware"""
        import datetime

        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            # Еслand проandзошла error, логandруем как 500
            status_code = 500
            raise
        finally:
            # Формandруем access log
            client_ip = request.client[0] if request.client else "-"
            timestamp = datetime.datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")
            method = request.method
            path = request.path
            if request.query_string:
                path += f"?{request.query_string}"

            # Размер responseа (прandблandзandтельный)
            size = "-"
            if hasattr(response, "content") and response.content:
                if isinstance(response.content, (str, bytes)):
                    size = str(len(response.content))

            referer = request.get_header("referer", "-")
            user_agent = request.get_header("user-agent", "-")

            log_entry = self.format_string.format(
                client=client_ip,
                timestamp=timestamp,
                method=method,
                path=path,
                status=status_code,
                size=size,
                referer=referer,
                user_agent=user_agent,
            )

            self.logger.info(log_entry)

        return response
