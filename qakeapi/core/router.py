from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union
import re
from dataclasses import dataclass
from .requests import Request
from .responses import Response

@dataclass
class Route:
    """Route class"""
    path: str
    handler: Callable
    methods: List[str]
    name: Optional[str] = None
    
    def __post_init__(self):
        """Компилируем регулярное выражение для пути"""
        pattern = self.path
        pattern = re.sub(r'{([^:}]+)(?::([^}]+))?}', lambda m: f'(?P<{m.group(1)}>[^/]+)', pattern)
        self.pattern = re.compile(f'^{pattern}$')
        
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
        
    def add_route(self, path: str, handler: Callable, methods: List[str] = None) -> None:
        """Add route to router"""
        if methods is None:
            methods = ["GET"]
        methods = [m.upper() for m in methods]
        
        route = Route(
            path=path,
            handler=handler,
            methods=methods
        )
        print(f"Added route: {path} {methods}")  # Debug log
        self.routes.append(route)
        
    def route(self, path: str, methods: List[str] = None):
        """Route decorator"""
        def decorator(handler: Callable) -> Callable:
            self.add_route(path, handler, methods)
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
        
    def find_route(self, path: str, method: str) -> Tuple[Optional[Route], Optional[Dict[str, str]]]:
        """Find route for path and method"""
        print(f"Looking for route: {path} {method}")  # Debug log
        print(f"Available routes: {[(r.path, r.methods) for r in self.routes]}")  # Debug log
        
        for route in self.routes:
            params = route.match(path)
            if params is not None and method in route.methods:
                print(f"Found matching route: {route.path}")  # Debug log
                return route, params
        print(f"No matching route found for {path} {method}")  # Debug log
        return None, None
        
    async def handle_request(self, request: Request) -> Response:
        """Handle incoming request"""
        try:
            route, params = self.find_route(request.path, request.method)
            if route is None:
                return Response.json({"detail": "Not Found"}, status_code=404)
                
            # Extract path parameters
            request.scope["path_params"] = params or {}
            
            # Apply middleware
            handler = route.handler
            for middleware in reversed(self._middleware):
                handler = middleware(handler)
                
            # Call handler
            response = await handler(request)
            return response
            
        except Exception as e:
            print(f"Error handling request: {str(e)}")
            return Response.json({"detail": "Internal Server Error"}, status_code=500)
            
    def _extract_path_params(self, pattern: str, path: str) -> dict:
        """Extract path parameters from URL"""
        pattern_parts = pattern.split("/")
        path_parts = path.split("/")
        
        params = {}
        for pattern_part, path_part in zip(pattern_parts, path_parts):
            if pattern_part.startswith("{") and pattern_part.endswith("}"):
                param_name = pattern_part[1:-1]
                params[param_name] = path_part
                
        return params
        
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