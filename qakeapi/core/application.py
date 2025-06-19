import asyncio
import json
import traceback
from functools import partial
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qs
import logging

from .background import BackgroundTask, BackgroundTaskManager
from .dependencies import DependencyContainer
from .openapi import OpenAPIGenerator, OpenAPIInfo, OpenAPIPath, get_swagger_ui_html
from .requests import Request
from .responses import Response
from .routing import Router
from .websockets import WebSocket, WebSocketState

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ASGIApplication:
    """Базовый класс ASGI-приложения"""

    def __init__(self):
        self.routes: Dict[str, Dict[str, Callable]] = {}
        self._middleware: List[Callable] = []
        self.startup_handlers: List[Callable] = []
        self.shutdown_handlers: List[Callable] = []
        self.background_tasks = BackgroundTaskManager()
        self.dependency_container = DependencyContainer()
        self.openapi_info = OpenAPIInfo()
        self.openapi_generator = OpenAPIGenerator(self.openapi_info)
        self.router = Router()

        # Добавляем специальные маршруты для OpenAPI
        async def docs(request: Request):
            return Response.html(
                get_swagger_ui_html("/openapi.json", self.openapi_info.title)
            )

        async def openapi(request: Request):
            return Response.json(self.openapi_generator.generate())

        self.router.add_route("/docs", docs, ["GET"])
        self.router.add_route("/openapi.json", openapi, ["GET"])

    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        """ASGI интерфейс"""
        if scope["type"] == "http":
            await self.handle_http(scope, receive, send)
        elif scope["type"] == "websocket":
            await self.handle_websocket(scope, receive, send)
        elif scope["type"] == "lifespan":
            await self.handle_lifespan(scope, receive, send)

    async def handle_http(
        self, scope: Dict[str, Any], receive: Callable, send: Callable
    ) -> None:
        """Handle HTTP request"""
        try:
            # Получаем тело запроса
            body = b""
            more_body = True

            while more_body:
                message = await receive()
                body += message.get("body", b"")
                more_body = message.get("more_body", False)

            # Создаем объект Request
            print(f"Creating request with scope: {scope}")
            request = Request(scope, body)
            request.dependency_container = self.dependency_container
            request.scope["dependency_container"] = self.dependency_container
            print(f"Request created: {request.method} {request.path}")

            # Находим маршрут
            route_info = self.router.find_route(request.path)
            if route_info is None:
                response = Response.json({"detail": "Not Found"}, status_code=404)
                await response(send)
                return

            route, params = route_info
            request.scope["path_params"] = params

            # Проверяем метод
            if request.method not in route.methods and request.method != "OPTIONS":
                response = Response.json(
                    {"detail": f"Method {request.method} not allowed"}, status_code=405
                )
                await response(send)
                return

            # Применяем middleware
            handler = route.handler
            for middleware in reversed(self._middleware):
                try:
                    new_handler = await middleware(request=request, handler=handler)
                    if new_handler is not None:
                        handler = new_handler
                except Exception as e:
                    print(f"Error applying middleware: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    response = Response.json({"detail": "Internal Server Error"}, status_code=500)
                    await response(send)
                    return

            # Вызываем обработчик
            try:
                response = await handler(request)
                if isinstance(response, Response):
                    await response(send)
                else:
                    await Response.json(response)(send)
            except Exception as e:
                print(f"Error in handler: {str(e)}")
                import traceback
                print(traceback.format_exc())
                response = Response.json({"detail": "Internal Server Error"}, status_code=500)
                await response(send)

        except Exception as e:
            print(f"Error handling request: {str(e)}")
            import traceback
            print(traceback.format_exc())
            response = Response.json({"detail": "Internal Server Error"}, status_code=500)
            await response(send)

    async def handle_websocket(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        """Обработка WebSocket соединений"""
        websocket = WebSocket(scope, receive, send)
        path = scope["path"]

        # Ищем обработчик для WebSocket
        handler = None
        for route_path, handlers in self.routes.items():
            if "websocket" in handlers and route_path == path:
                handler = handlers["websocket"]
                break

        if handler:
            try:
                await handler(websocket)
            except Exception as e:
                if websocket.state == WebSocket.State.CONNECTED:
                    await websocket.close(1011)  # Internal error
        else:
            await send({"type": "websocket.close", "code": 403})

    async def handle_lifespan(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]],
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

    async def build_request(
        self, scope: Dict[str, Any], receive: Callable
    ) -> Dict[str, Any]:
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
            "body": body,
        }

    async def handle_request(self, request: Request) -> Response:
        """Handle incoming request"""
        try:
            route_info = self.router.find_route(request.path)
            if route_info is None:
                return Response.json({"detail": "Not Found"}, status_code=404)

            route, params = route_info
            request.scope["path_params"] = params

            # Let middleware handle OPTIONS requests
            if request.method == "OPTIONS":
                return Response.json({}, status_code=200)

            # Check if method is allowed
            if request.method not in route.methods:
                return Response.json(
                    {"detail": f"Method {request.method} not allowed"}, status_code=405
                )

            # Apply middleware first
            handler = route.handler
            for middleware in reversed(self._middleware):
                try:
                    if asyncio.iscoroutinefunction(middleware):
                        next_handler = await middleware(request, handler)
                    else:
                        next_handler = middleware(request, handler)
                    
                    if isinstance(next_handler, Response):
                        return next_handler
                    handler = next_handler
                except Exception as e:
                    print(f"Error in middleware: {str(e)}")
                    continue

            # Call the final handler
            print(f"Calling final handler: {handler}")
            response = await handler(request)
            print(f"Final response: {response}")
            return response

        except Exception as e:
            # Log the error
            print(f"Error handling request: {str(e)}")
            print(traceback.format_exc())
            return Response.json({"detail": "Internal Server Error"}, status_code=500)

    async def execute_middleware_chain(
        self, handler: Callable, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute middleware chain and return response"""

        async def execute_next(
            request: Dict[str, Any], next_middleware_idx: int
        ) -> Dict[str, Any]:
            if next_middleware_idx >= len(self._middleware):
                return await handler(request)
            return await self._middleware[next_middleware_idx](
                request, lambda r: execute_next(r, next_middleware_idx + 1)
            )

        return await execute_next(request, 0)

    async def send_response(self, send: Callable, response: Dict[str, Any]) -> None:
        """Send response through ASGI interface"""
        if hasattr(response, "to_dict"):  # Handle Response objects
            response = response.to_dict()

        await send(
            {
                "type": "http.response.start",
                "status": response["status"],
                "headers": response["headers"],
            }
        )

        await send({"type": "http.response.body", "body": response["body"]})

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
        self._middleware.append(middleware_func)
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
        **kwargs: Any,
    ) -> str:
        """Добавить фоновую задачу"""
        task = BackgroundTask(
            func,
            *args,
            task_id=task_id,
            timeout=timeout,
            retry_count=retry_count,
            **kwargs,
        )
        return await self.background_tasks.add_task(task)

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Получить статус фоновой задачи"""
        return self.background_tasks.get_task_status(task_id)

    async def cancel_background_task(self, task_id: str) -> bool:
        """Отменить фоновую задачу"""
        return await self.background_tasks.cancel_task(task_id)

    def get(self, path: str, **kwargs):
        """GET route decorator"""

        def decorator(handler: Callable):
            print(f"Registering GET route: {path}")
            # Store OpenAPI metadata in handler
            handler.openapi_metadata = {
                "summary": kwargs.get("summary", ""),
                "description": kwargs.get("description", ""),
                "response_model": kwargs.get("response_model"),
                "tags": kwargs.get("tags", []),
            }
            self.router.add_route(path, handler, ["GET"])
            return handler

        return decorator

    def post(self, path: str, **kwargs):
        """POST route decorator"""

        def decorator(handler: Callable):
            # Store OpenAPI metadata in handler
            handler.openapi_metadata = {
                "summary": kwargs.get("summary", ""),
                "description": kwargs.get("description", ""),
                "request_model": kwargs.get("request_model"),
                "response_model": kwargs.get("response_model"),
                "tags": kwargs.get("tags", []),
            }
            self.router.add_route(path, handler, ["POST"])
            return handler

        return decorator

    def put(self, path: str, **kwargs):
        """PUT route decorator"""

        def decorator(handler: Callable):
            self.router.add_route(path, handler, ["PUT"])
            path_info = OpenAPIPath(path=path, method="PUT", **kwargs)
            self.openapi_generator.add_path(path_info)
            return handler

        return decorator

    def delete(self, path: str, **kwargs):
        """DELETE route decorator"""

        def decorator(handler: Callable):
            self.router.add_route(path, handler, ["DELETE"])
            path_info = OpenAPIPath(path=path, method="DELETE", **kwargs)
            self.openapi_generator.add_path(path_info)
            return handler

        return decorator

    def patch(self, path: str, **kwargs):
        """PATCH route decorator"""

        def decorator(handler: Callable):
            self.router.add_route(path, handler, ["PATCH"])
            path_info = OpenAPIPath(path=path, method="PATCH", **kwargs)
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
                path_info = OpenAPIPath(path=path, method=method, **kwargs)
                self.openapi_generator.add_path(path_info)
            return handler

        return decorator

    def websocket(self, path: str):
        """Decorator for WebSocket routes"""

        def decorator(handler):
            self.router.add_websocket_route(path, handler)
            return handler

        return decorator

    def options(self, path: str, **kwargs):
        """OPTIONS route decorator"""

        def decorator(handler: Callable):
            self.router.add_route(path, handler, ["OPTIONS"])
            path_info = OpenAPIPath(path=path, method="OPTIONS", **kwargs)
            self.openapi_generator.add_path(path_info)
            return handler

        return decorator

    @property
    def middleware(self) -> list:
        """Get middleware list"""
        return self._middleware


class Application(ASGIApplication):
    """Main application class"""

    def __init__(
        self, title: str = "QakeAPI", version: str = "1.0.0", description: str = ""
    ):
        super().__init__()
        self.title = title
        self.version = version
        self.description = description
        self.router = Router()
        self._middleware = []
        self.background_tasks = BackgroundTaskManager()
        self.openapi_generator = OpenAPIGenerator(
            OpenAPIInfo(title=title, version=version, description=description)
        )

        # Add default routes
        self.router.add_route("/docs", self.swagger_ui, ["GET"])
        self.router.add_route("/openapi.json", self.openapi_schema, ["GET"])

    @property
    def middleware(self) -> list:
        """Get middleware list"""
        return self._middleware

    def add_middleware(self, middleware_func: Callable) -> None:
        """Add middleware to the application"""
        self._middleware.append(middleware_func)

    async def handle_request(self, request: Request) -> Response:
        """Handle incoming request"""
        try:
            route_info = self.router.find_route(request.path)
            if route_info is None:
                return Response.json({"detail": "Not Found"}, status_code=404)

            route, params = route_info
            request.scope["path_params"] = params

            # Let middleware handle OPTIONS requests
            if request.method == "OPTIONS":
                return Response.json({}, status_code=200)

            # Check if method is allowed
            if request.method not in route.methods:
                return Response.json(
                    {"detail": f"Method {request.method} not allowed"}, status_code=405
                )

            # Apply middleware first
            handler = route.handler
            for middleware in reversed(self._middleware):
                try:
                    if asyncio.iscoroutinefunction(middleware):
                        next_handler = await middleware(request, handler)
                    else:
                        next_handler = middleware(request, handler)
                    
                    if isinstance(next_handler, Response):
                        return next_handler
                    handler = next_handler
                except Exception as e:
                    print(f"Error in middleware: {str(e)}")
                    continue

            # Call the final handler
            print(f"Calling final handler: {handler}")
            response = await handler(request)
            print(f"Final response: {response}")
            return response

        except Exception as e:
            # Log the error
            print(f"Error handling request: {str(e)}")
            print(traceback.format_exc())
            return Response.json({"detail": "Internal Server Error"}, status_code=500)

    async def handle_http(
        self, scope: Dict[str, Any], receive: Callable, send: Callable
    ) -> None:
        """Handle HTTP request"""
        try:
            # Получаем тело запроса
            body = b""
            more_body = True

            while more_body:
                message = await receive()
                body += message.get("body", b"")
                more_body = message.get("more_body", False)

            # Создаем объект Request
            print(f"Creating request with scope: {scope}")
            request = Request(scope, body)
            request.dependency_container = self.dependency_container
            request.scope["dependency_container"] = self.dependency_container
            print(f"Request created: {request.method} {request.path}")

            # Находим маршрут
            route_info = self.router.find_route(request.path)
            if route_info is None:
                response = Response.json({"detail": "Not Found"}, status_code=404)
                await response(send)
                return

            route, params = route_info
            request.scope["path_params"] = params

            # Проверяем метод
            if request.method not in route.methods and request.method != "OPTIONS":
                response = Response.json(
                    {"detail": f"Method {request.method} not allowed"}, status_code=405
                )
                await response(send)
                return

            # Применяем middleware
            handler = route.handler
            for middleware in reversed(self._middleware):
                try:
                    new_handler = await middleware(request=request, handler=handler)
                    if new_handler is not None:
                        handler = new_handler
                except Exception as e:
                    print(f"Error applying middleware: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    response = Response.json({"detail": "Internal Server Error"}, status_code=500)
                    await response(send)
                    return

            # Вызываем обработчик
            try:
                response = await handler(request)
                if isinstance(response, Response):
                    await response(send)
                else:
                    await Response.json(response)(send)
            except Exception as e:
                print(f"Error in handler: {str(e)}")
                import traceback
                print(traceback.format_exc())
                response = Response.json({"detail": "Internal Server Error"}, status_code=500)
                await response(send)

        except Exception as e:
            print(f"Error handling request: {str(e)}")
            import traceback
            print(traceback.format_exc())
            response = Response.json({"detail": "Internal Server Error"}, status_code=500)
            await response(send)

    async def handle_websocket(self, scope: Dict, receive: Any, send: Any) -> None:
        """Handle WebSocket connections"""
        websocket = WebSocket(scope, receive, send)
        path = scope["path"]

        # Find route
        route_info = self.router.find_route(path, "websocket")
        if not route_info:
            await send({"type": "websocket.close", "code": 1008})  # Policy violation
            return

        route, params = route_info
        scope["path_params"] = params

        # Apply middleware
        handler = route.handler

        try:
            await handler(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}", exc_info=True)
            if websocket.state == WebSocketState.CONNECTED:
                await websocket.close(1011)  # Internal error
            else:
                await send({"type": "websocket.close", "code": 1011})

    async def handle_lifespan(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]],
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
        for handler in self.startup_handlers:
            await handler()

    async def shutdown(self) -> None:
        """Действия при остановке приложения"""
        for handler in self.shutdown_handlers:
            await handler()
        await self.dependency_container.cleanup_all()

    async def swagger_ui(self, request: Request):
        return Response.html(get_swagger_ui_html("/openapi.json", self.title))

    async def openapi_schema(self, request: Request):
        """Generate and return OpenAPI schema"""
        print("Generating OpenAPI schema...")
        schema = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description,
            },
            "paths": {},
        }

        # Add paths from router
        print(
            f"Available routes: {[(r.path, r.type, r.methods) for r in self.router.routes]}"
        )
        for route in self.router.routes:
            if route.type != "http":
                continue

            print(f"Processing route: {route.path} {route.methods}")
            print(
                f"Handler metadata: {getattr(route.handler, 'openapi_metadata', None)}"
            )

            if route.path not in schema["paths"]:
                schema["paths"][route.path] = {}

            for method in route.methods:
                method = method.lower()
                metadata = getattr(route.handler, "openapi_metadata", {}) or {}

                path_data = {
                    "summary": metadata.get("summary", ""),
                    "description": metadata.get("description", ""),
                    "tags": metadata.get("tags", []),
                    "parameters": [],
                    "responses": {"200": {"description": "Successful response"}},
                }

                # Add path parameters
                if "{" in route.path:
                    param_names = [
                        p[1:-1]
                        for p in route.path.split("/")
                        if p.startswith("{") and p.endswith("}")
                    ]
                    for param_name in param_names:
                        path_data["parameters"].append(
                            {
                                "name": param_name,
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        )

                # Add request body schema if present
                if metadata.get("request_model"):
                    path_data["requestBody"] = {
                        "content": {
                            "application/json": {
                                "schema": metadata["request_model"].model_json_schema()
                            }
                        },
                        "required": True,
                    }

                # Add response schema if present
                if metadata.get("response_model"):
                    path_data["responses"]["200"]["content"] = {
                        "application/json": {
                            "schema": metadata["response_model"].model_json_schema()
                        }
                    }

                schema["paths"][route.path][method] = path_data

        print("Generated schema:", schema)
        return Response(
            content=json.dumps(schema, indent=2),
            status_code=200,
            headers=[
                (b"content-type", b"application/json"),
                (b"access-control-allow-origin", b"*"),
                (b"cache-control", b"no-cache"),
            ],
        )
