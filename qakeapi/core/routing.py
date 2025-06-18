import logging
import re
import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union

from .requests import Request
from .responses import Response, JSONResponse
from .websockets import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class Route:
    """Маршрут"""

    path: str
    handler: Callable
    methods: List[str]
    name: Optional[str] = None
    type: str = "http"  # "http" или "websocket"

    def __post_init__(self):
        """Компилируем регулярное выражение для пути"""
        self.pattern = self._compile_pattern(self.path)
        logger.debug(f"Created route: {self.path} {self.methods} {self.type}")

    def _compile_pattern(self, path: str) -> Pattern:
        """Компилируем паттерн пути в регулярное выражение"""
        pattern = re.sub(r"{([^:}]+)(?::([^}]+))?}", r"(?P<\1>[^/]+)", path)
        return re.compile(f"^{pattern}$")

    def match(self, path: str) -> Optional[Dict[str, str]]:
        """Проверить совпадение пути с маршрутом"""
        match = self.pattern.match(path)
        if match:
            return match.groupdict()
        return None


class Router:
    """Маршрутизатор запросов"""

    def __init__(self):
        self.routes: List[Route] = []
        self._middleware: List[Callable] = []

    def add_route(
        self,
        path: str,
        handler: Callable,
        methods: List[str] = None,
        name: Optional[str] = None,
        route_type: str = "http"
    ) -> None:
        """Добавить маршрут"""
        if methods is None:
            methods = ["GET"]
        methods = [method.upper() for method in methods]

        # Проверяем существующий маршрут
        for existing_route in self.routes:
            if existing_route.path == path and existing_route.type == route_type:
                # Обновляем существующий маршрут
                existing_route.handler = handler
                existing_route.methods = methods
                existing_route.name = name
                logger.debug(f"Updated route: {path} {methods}")
                return

        route = Route(path, handler, methods, name, type=route_type)
        self.routes.append(route)
        logger.debug(f"Added route: {path} {methods}")

    def route(
        self, path: str, methods: List[str] = None, name: Optional[str] = None
    ) -> Callable:
        """Декоратор для добавления маршрута"""
        def decorator(handler: Callable) -> Callable:
            self.add_route(path, handler, methods, name)
            return handler
        return decorator

    def add_middleware(self, middleware: Callable) -> None:
        """Добавить middleware"""
        self._middleware.append(middleware)

    def middleware(self) -> Callable:
        """Декоратор для добавления middleware"""
        def decorator(middleware: Callable) -> Callable:
            self.add_middleware(middleware)
            return middleware
        return decorator

    def find_route(
        self, path: str, type: str = "http"
    ) -> Optional[Tuple[Route, Dict[str, str]]]:
        """Найти маршрут для пути"""
        logger.debug(f"Finding route for path: {path} type: {type}")
        logger.debug(f"Available routes: {[(r.path, r.type, r.methods) for r in self.routes]}")

        for route in self.routes:
            if route.type != type:
                continue

            params = route.match(path)
            if params is not None:
                logger.debug(f"Found route: {route.path} {route.methods}")
                return route, params

        logger.debug(f"No route found for path: {path}")
        return None

    async def handle_request(self, request: Union[Request, Dict[str, Any]]) -> Union[Response, Dict[str, Any]]:
        """Обработать запрос"""
        try:
            # Определяем тип запроса и получаем параметры
            if isinstance(request, dict):
                path = request["path"]
                method = request["method"].upper()
                request_type = request.get("type", "http")
            else:
                path = request.path
                method = request.method.upper()
                request_type = getattr(request, "type", "http")

            logger.debug(f"Handling request: {method} {path}")

            # Ищем маршрут
            route_info = self.find_route(path, request_type)
            if route_info is None:
                logger.debug(f"No route found for {path}")
                if isinstance(request, dict):
                    return {
                        "status": 404,
                        "headers": [(b"content-type", b"application/json")],
                        "body": b'{"detail": "Not Found"}',
                    }
                return Response.json({"detail": "Not Found"}, status_code=404)

            route, params = route_info

            # Обрабатываем OPTIONS запросы
            if method == "OPTIONS":
                return Response.json({}, status_code=200)

            # Проверяем метод
            if method not in route.methods:
                logger.debug(f"Method {method} not allowed for {path}")
                if isinstance(request, dict):
                    return {
                        "status": 405,
                        "headers": [(b"content-type", b"application/json")],
                        "body": b'{"detail": "Method Not Allowed"}',
                    }
                return Response.json({"detail": "Method Not Allowed"}, status_code=405)

            # Добавляем параметры пути
            if isinstance(request, dict):
                request["path_params"] = params
            else:
                request.path_params.update(params or {})

            # Применяем middleware
            handler = route.handler
            for middleware in reversed(self._middleware):
                try:
                    if asyncio.iscoroutinefunction(middleware):
                        prev_handler = handler
                        async def wrapped_handler(req, prev_handler=prev_handler):
                            return await middleware(req, prev_handler)
                        handler = wrapped_handler
                    else:
                        handler = middleware(handler)
                except Exception as e:
                    logger.error(f"Error applying middleware: {e}")
                    raise

            # Вызываем обработчик
            logger.debug(f"Calling handler for {path}")
            response = await handler(request)
            logger.debug(f"Handler response: {response}")
            return response

        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            import traceback
            traceback.print_exc()

            if isinstance(request, dict):
                return {
                    "status": 500,
                    "headers": [(b"content-type", b"application/json")],
                    "body": b'{"detail": "Internal Server Error"}',
                }
            return Response.json({"detail": "Internal Server Error"}, status_code=500)

    def url_for(self, name: str, **params: Any) -> str:
        """Сгенерировать URL для именованного маршрута"""
        for route in self.routes:
            if route.name == name:
                path = route.path
                for key, value in params.items():
                    path = path.replace(f"{{{key}}}", str(value))
                return path
        raise ValueError(f"No route found with name '{name}'")

    def add_websocket_route(self, path: str, handler: Callable) -> None:
        """Добавить WebSocket маршрут"""
        self.add_route(path, handler, ["GET"], route_type="websocket")
