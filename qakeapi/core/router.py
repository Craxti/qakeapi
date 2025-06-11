from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union
import re
from dataclasses import dataclass
from .requests import Request

@dataclass
class Route:
    """Маршрут"""
    path: str
    handler: Callable
    methods: List[str]
    name: Optional[str] = None
    
    def __post_init__(self):
        """Компилируем регулярное выражение для пути"""
        # Заменяем параметры пути на именованные группы
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
        
    def add_route(
        self,
        path: str,
        handler: Callable,
        methods: List[str] = None,
        name: Optional[str] = None
    ) -> None:
        """Добавить маршрут"""
        if methods is None:
            methods = ["GET"]
        methods = [method.upper() for method in methods]
        route = Route(path, handler, methods, name)
        self.routes.append(route)
        print(f"Added route: {path} {methods}")  # Debug log
        
    def route(self, path: str, methods: List[str] = None, name: str = None):
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
        
    def find_route(self, path: str, method: str) -> Tuple[Optional[Route], Optional[Dict[str, str]]]:
        """Найти маршрут для пути и метода"""
        print(f"Looking for route: {path} {method}")  # Debug log
        print(f"Available routes: {[(r.path, r.methods) for r in self.routes]}")  # Debug log
        
        for route in self.routes:
            params = route.match(path)
            if params is not None and method in route.methods:
                print(f"Found matching route: {route.path}")  # Debug log
                return route, params
        print(f"No matching route found for {path} {method}")  # Debug log
        return None, None
        
    async def handle_request(self, raw_request: Dict[str, Any]) -> Dict[str, Any]:
        """Обработать запрос"""
        path = raw_request["path"]
        method = raw_request["method"].upper()
        
        # Ищем маршрут
        route, params = self.find_route(path, method)
        if route is None:
            return {
                "status": 404,
                "headers": [(b"content-type", b"application/json")],
                "body": b'{"detail": "Not Found"}'
            }
            
        # Создаем объект Request
        raw_request["path_params"] = params
        request = Request(raw_request, raw_request.get("body", b""))
        
        # Выполняем цепочку middleware
        handler = route.handler
        for middleware in reversed(self._middleware):
            handler = middleware(handler)
            
        # Вызываем обработчик с параметрами пути
        try:
            if params:
                response = await handler(request, **params)
            else:
                response = await handler(request)
            return response
        except Exception as e:
            print(f"Error handling request: {e}")  # Debug log
            return {
                "status": 500,
                "headers": [(b"content-type", b"application/json")],
                "body": b'{"detail": "Internal Server Error"}'
            }
        
    def url_for(self, name: str, **params: Any) -> str:
        """Generate URL for named route"""
        for route in self.routes:
            if route.name == name:
                path = route.path
                for key, value in params.items():
                    path = path.replace(f"{{{key}}}", str(value))
                return path
        raise ValueError(f"No route found with name '{name}'") 