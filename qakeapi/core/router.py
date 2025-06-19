import logging
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union

from .requests import Request
from .responses import Response
from .websockets import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class Route:
    """Route class"""

    path: str
    handler: Callable
    methods: List[str]
    name: Optional[str] = None
    type: str = "http"  # "http" или "websocket"

    def __post_init__(self):
        """Компилируем регулярное выражение для пути"""
        self.pattern = self._compile_pattern(self.path)
        logger.debug(f"Created route: {self.path} {self.methods} {self.type}")

    def _compile_pattern(self, path: str) -> re.Pattern:
        """Compile path pattern to regex"""
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
        self, path: str, handler: Callable, methods: List[str] = None, route_type: str = "http"
    ) -> None:
        """Add route"""
        if methods is None:
            methods = ["GET"]
        methods = [m.upper() for m in methods]

        # Check if route already exists
        for existing_route in self.routes:
            if existing_route.path == path and existing_route.type == route_type:
                # Update existing route instead of adding a new one
                existing_route.handler = handler
                existing_route.methods = methods
                logger.debug(f"Updated route: {path} {methods} [{route_type}]")
                return

        route = Route(path=path, handler=handler, methods=methods, type=route_type)
        self.routes.append(route)
        logger.debug(f"Added route: {path} {methods} [{route_type}]")

    def add_websocket_route(self, path: str, handler: Callable) -> None:
        """Add WebSocket route"""
        self.add_route(path, handler, ["GET"], route_type="websocket")

    def find_route(self, path: str, route_type: str = "http") -> Optional[Tuple[Route, Dict[str, str]]]:
        """Find route by path and type"""
        logger.debug(f"Finding route for path: {path} type: {route_type}")
        logger.debug(f"Available routes: {[(r.path, r.type, r.methods) for r in self.routes]}")
        
        for route in self.routes:
            if route.type == route_type:
                params = route.match(path)
                if params is not None:
                    logger.debug(f"Found route: {route.path} [{route.type}]")
                    return route, params
        
        logger.debug(f"No route found for path: {path} type: {route_type}")
        return None

    def route(self, path: str, methods: List[str] = None):
        """Route decorator"""

        def decorator(handler: Callable) -> Callable:
            self.add_route(path, handler, methods)
            return handler

        return decorator

    def websocket(self, path: str):
        """WebSocket route decorator"""

        def decorator(handler: Callable) -> Callable:
            self.add_websocket_route(path, handler)
            return handler

        return decorator

    def add_middleware(self, middleware: Callable) -> None:
        """Добавить middleware"""
        self._middleware.append(middleware)

    def middleware(self) -> Callable:
        """Декоратор для добавления middleware"""

        def decorator(middleware: Callable) -> Callable:
            self._middleware.append(middleware)
            return middleware

        return decorator

    async def handle_request(self, request: Request) -> Response:
        """Handle incoming request"""
        try:
            logger.debug(f"Handling request: {request.method} {request.path}")
            print(
                f"Available routes: {[(r.path, r.type, r.methods) for r in self.routes]}"
            )

            route_info = self.find_route(request.path)
            if route_info is None:
                print(f"No route found for {request.path}")
                response = Response.json({"detail": "Not Found"}, status_code=404)
                print(f"Response: {response.to_dict()}")
                return response

            route, params = route_info
            print(f"Found route: {route.path} {route.type} {route.methods}")

            # Handle OPTIONS requests specially
            if request.method == "OPTIONS":
                # If the route exists, allow OPTIONS
                return Response.json({}, status_code=200)

            # Check if method is allowed
            if request.method not in route.methods:
                print(f"Method {request.method} not allowed for {request.path}")
                response = Response.json(
                    {"detail": f"Method {request.method} not allowed"}, status_code=405
                )
                print(f"Response: {response.to_dict()}")
                return response

            # Extract path parameters
            request.scope["path_params"] = params

            # Apply middleware
            handler = route.handler
            for middleware in reversed(self._middleware):
                handler = middleware(handler)

            # Call handler
            print(f"Calling handler for {request.path}")
            response = await handler(request)
            print(f"Handler response: {response.to_dict()}")
            return response

        except Exception as e:
            print(f"Error handling request: {str(e)}")
            import traceback

            traceback.print_exc()
            response = Response.json(
                {"detail": "Internal Server Error"}, status_code=500
            )
            print(f"Error response: {response.to_dict()}")
            return response

    def url_for(self, name: str, **params: Any) -> str:
        """Generate URL for named route"""
        for route in self.routes:
            if route.name == name:
                path = route.path
                for key, value in params.items():
                    path = path.replace(f"{{{key}}}", str(value))
                return path
        raise ValueError(f"No route found with name '{name}'")

    def _match_route(self, pattern: str, path: str) -> Optional[Dict[str, str]]:
        """Match route pattern against path and extract parameters"""
        pattern_parts = pattern.split("/")
        path_parts = path.split("/")

        if len(pattern_parts) != len(path_parts):
            return None

        params = {}
        for pattern_part, path_part in zip(pattern_parts, path_parts):
            if pattern_part.startswith("{") and pattern_part.endswith("}"):
                param_name = pattern_part[1:-1]
                params[param_name] = path_part
            elif pattern_part != path_part:
                return None

        return params
