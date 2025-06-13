import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union

from .requests import Request
from .responses import Response


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
        # Заменяем параметры пути на именованные группы
        pattern = self.path
        pattern = re.sub(
            r"{([^:}]+)(?::([^}]+))?}", lambda m: f"(?P<{m.group(1)}>[^/]+)", pattern
        )
        self.pattern = re.compile(f"^{pattern}$")

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
    ) -> None:
        """Добавить маршрут"""
        if methods is None:
            methods = ["GET"]
        methods = [method.upper() for method in methods]
        route = Route(path, handler, methods, name)
        self.routes.append(route)

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

    def find_route(self, path: str, type: str = "http") -> Optional[Route]:
        """Найти маршрут для пути и метода"""
        print(f"Looking for route: {path} {type}")
        print(f"Available routes: {[(r.path, r.methods) for r in self.routes]}")

        for route in self.routes:
            if route.type == type:
                match = route.pattern.match(path)
                if match:
                    return route
        print(f"No matching route found for {path} {type}")
        return None

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Обработать запрос"""
        path = request["path"]
        method = request["method"].upper()

        # Ищем маршрут
        route = self.find_route(path)
        if route is None:
            return {
                "status": 404,
                "headers": [(b"content-type", b"application/json")],
                "body": b'{"detail": "Not Found"}',
            }

        # Добавляем параметры пути в запрос
        request["path_params"] = route.match(path)

        # Выполняем цепочку middleware
        handler = route.handler
        for middleware in reversed(self._middleware):
            handler = middleware(handler)

        # Вызываем обработчик
        return await handler(request)

    def url_for(self, name: str, **params: Any) -> str:
        """Generate URL for named route"""
        for route in self.routes:
            if route.name == name:
                path = route.path
                for key, value in params.items():
                    path = path.replace(f"{{{key}}}", str(value))
                return path
        raise ValueError(f"No route found with name '{name}'")

    def add_websocket_route(self, path: str, handler: Callable) -> None:
        """Add WebSocket route"""
        pattern = self._compile_pattern(path)
        route = Route(pattern, ["GET"], handler, path, "websocket")
        self.routes.append(route)
        print(f"Added WebSocket route: {path}")

    def _compile_pattern(self, path: str) -> Pattern:
        """Compile path pattern to regex"""
        # Replace path parameters with named capture groups
        pattern = re.sub(
            r"{([^:}]+)(?::([^}]+))?}", lambda m: f"(?P<{m.group(1)}>[^/]+)", path
        )
        return re.compile(f"^{pattern}$")
