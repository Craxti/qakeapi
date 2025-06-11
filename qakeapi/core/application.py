from typing import Any, Callable, Dict, List, Optional, Tuple, Union, Awaitable
import asyncio
from urllib.parse import parse_qs
from .background import BackgroundTask, BackgroundTaskManager
from .dependencies import DependencyContainer
from .router import Router
from .openapi import OpenAPIInfo, OpenAPIGenerator, OpenAPIPath, get_swagger_ui_html
from .requests import Request
import json
from .responses import Response

class ASGIApplication:
    """Базовый класс ASGI-приложения"""
    
    def __init__(self):
        self.routes: Dict[str, Dict[str, Callable]] = {}
        self.middleware: List[Callable] = []
        self.startup_handlers: List[Callable] = []
        self.shutdown_handlers: List[Callable] = []
        self.background_tasks = BackgroundTaskManager()
        self.dependency_container = DependencyContainer()
        self.openapi_info = OpenAPIInfo()
        self.openapi_generator = OpenAPIGenerator(self.openapi_info)
        self.router = Router()
        
        # Добавляем специальные маршруты для OpenAPI
        @self.router.route("/docs")
        async def docs(request: Request):
            return Response.html(get_swagger_ui_html("/openapi.json", self.openapi_info.title))
            
        @self.router.route("/openapi.json")
        async def openapi(request: Request):
            return Response.json(self.openapi_generator.generate())
        
    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """ASGI интерфейс"""
        if scope["type"] == "http":
            await self.handle_http(scope, receive, send)
        elif scope["type"] == "websocket":
            await self.handle_websocket(scope, receive, send)
        elif scope["type"] == "lifespan":
            await self.handle_lifespan(scope, receive, send)
            
    async def handle_http(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        """Handle HTTP request"""
        # Получаем тело запроса
        body = b""
        more_body = True
        
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)
            
        # Создаем объект Request
        request = Request(scope, body)
        
        # Проверяем специальные маршруты для OpenAPI
        if request.path == "/docs":
            response = Response.html(get_swagger_ui_html("/openapi.json", self.openapi_info.title))
        elif request.path == "/openapi.json":
            response = Response.json(self.openapi_generator.generate())
        else:
            # Обрабатываем запрос через роутер
            response = await self.router.handle_request(request)
        
        # Отправляем ответ
        await response(send)
        
    async def handle_websocket(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Обработка WebSocket соединений"""
        # Пока просто закрываем соединение
        await send({"type": "websocket.close"})
        
    async def handle_lifespan(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Обработка событий жизненного цикла"""
        while True:
            message = await receive()
            
            if message["type"] == "lifespan.startup":
                await self.startup()
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await self.shutdown()
                await send({"type": "lifespan.shutdown.complete"})
                break
                
    async def startup(self) -> None:
        """Действия при запуске приложения"""
        pass
        
    async def shutdown(self) -> None:
        """Действия при остановке приложения"""
        await self.dependency_container.cleanup_all()
        
    async def build_request(self, scope: Dict[str, Any], receive: Callable) -> Dict[str, Any]:
        """Build request object from ASGI scope"""
        body = b""
        more_body = True
        
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)
            
        return {
            "scope": scope,
            "method": scope["method"],
            "path": scope["path"],
            "query_params": parse_qs(scope.get("query_string", b"").decode()),
            "headers": dict(scope.get("headers", [])),
            "body": body
        }
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка запроса"""
        path = request["path"]
        method = request["method"].upper()

        # Проверяем специальные маршруты для OpenAPI
        if path == "/docs":
            return Response.html(get_swagger_ui_html("/openapi.json", self.openapi_info.title))
        elif path == "/openapi.json":
            return Response.json(self.openapi_generator.generate())

        return await self.router.handle_request(request)
        
    async def execute_middleware_chain(
        self, handler: Callable, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute middleware chain and return response"""
        async def execute_next(request: Dict[str, Any], next_middleware_idx: int) -> Dict[str, Any]:
            if next_middleware_idx >= len(self.middleware):
                return await handler(request)
            return await self.middleware[next_middleware_idx](
                request, lambda r: execute_next(r, next_middleware_idx + 1)
            )
            
        return await execute_next(request, 0)
        
    async def send_response(self, send: Callable, response: Dict[str, Any]) -> None:
        """Send response through ASGI interface"""
        if hasattr(response, "to_dict"):  # Handle Response objects
            response = response.to_dict()
            
        await send({
            "type": "http.response.start",
            "status": response["status"],
            "headers": response["headers"]
        })
        
        await send({
            "type": "http.response.body",
            "body": response["body"]
        })
        
    def route(self, path: str, methods: List[str] = None):
        """Route decorator for registering HTTP handlers"""
        if methods is None:
            methods = ["get"]
            
        def decorator(handler: Callable):
            if path not in self.routes:
                self.routes[path] = {}
            for method in methods:
                self.routes[path][method.lower()] = handler
            return handler
        return decorator
        
    def websocket(self, path: str):
        """WebSocket route decorator"""
        def decorator(handler: Callable):
            if path not in self.routes:
                self.routes[path] = {}
            self.routes[path]["websocket"] = handler
            return handler
        return decorator
        
    def middleware(self, middleware_func: Callable):
        """Middleware decorator"""
        self.middleware.append(middleware_func)
        return middleware_func
        
    def on_startup(self, handler: Callable):
        """Register startup handler"""
        self.startup_handlers.append(handler)
        return handler
        
    def on_shutdown(self, handler: Callable):
        """Register shutdown handler"""
        self.shutdown_handlers.append(handler)
        return handler
        
    async def add_background_task(
        self,
        func: Callable,
        *args: Any,
        task_id: Optional[str] = None,
        timeout: Optional[float] = None,
        retry_count: int = 0,
        **kwargs: Any
    ) -> str:
        """Добавить фоновую задачу"""
        task = BackgroundTask(
            func,
            *args,
            task_id=task_id,
            timeout=timeout,
            retry_count=retry_count,
            **kwargs
        )
        return await self.background_tasks.add_task(task)
        
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Получить статус фоновой задачи"""
        return self.background_tasks.get_task_status(task_id)
        
    async def cancel_background_task(self, task_id: str) -> bool:
        """Отменить фоновую задачу"""
        return await self.background_tasks.cancel_task(task_id)

class Application(ASGIApplication):
    """Основной класс приложения"""
    
    def __init__(self, title: str = "API Documentation", version: str = "1.0.0", description: str = ""):
        super().__init__()
        self.openapi_info = OpenAPIInfo(title, version, description)
        self.openapi_generator = OpenAPIGenerator(self.openapi_info)

    def get(self, path: str, **kwargs):
        """GET route decorator"""
        def decorator(handler: Callable):
            self.router.add_route(path, handler, ["GET"])
            path_info = OpenAPIPath(
                path=path,
                method="GET",
                **kwargs
            )
            self.openapi_generator.add_path(path_info)
            return handler
        return decorator

    def post(self, path: str, **kwargs):
        """POST route decorator"""
        def decorator(handler: Callable):
            self.router.add_route(path, handler, ["POST"])
            path_info = OpenAPIPath(
                path=path,
                method="POST",
                **kwargs
            )
            self.openapi_generator.add_path(path_info)
            return handler
        return decorator

    def put(self, path: str, **kwargs):
        """PUT route decorator"""
        def decorator(handler: Callable):
            self.router.add_route(path, handler, ["PUT"])
            path_info = OpenAPIPath(
                path=path,
                method="PUT",
                **kwargs
            )
            self.openapi_generator.add_path(path_info)
            return handler
        return decorator

    def delete(self, path: str, **kwargs):
        """DELETE route decorator"""
        def decorator(handler: Callable):
            self.router.add_route(path, handler, ["DELETE"])
            path_info = OpenAPIPath(
                path=path,
                method="DELETE",
                **kwargs
            )
            self.openapi_generator.add_path(path_info)
            return handler
        return decorator

    def patch(self, path: str, **kwargs):
        """PATCH route decorator"""
        def decorator(handler: Callable):
            self.router.add_route(path, handler, ["PATCH"])
            path_info = OpenAPIPath(
                path=path,
                method="PATCH",
                **kwargs
            )
            self.openapi_generator.add_path(path_info)
            return handler
        return decorator

    def api_route(self, path: str, methods: List[str] = None, **kwargs):
        """API route decorator"""
        if methods is None:
            methods = ["GET"]
        methods = [m.upper() for m in methods]

        def decorator(handler: Callable):
            self.router.add_route(path, handler, methods)
            for method in methods:
                path_info = OpenAPIPath(
                    path=path,
                    method=method,
                    **kwargs
                )
                self.openapi_generator.add_path(path_info)
            return handler
        return decorator 