"""
Main QakeAPI application class
"""
import traceback
from typing import Any, Callable, Dict, List, Optional, Sequence, Union
import logging

from .request import Request
from .response import Response, JSONResponse, PlainTextResponse
from .router import APIRouter, RouteType
from .websocket import WebSocket
from .exceptions import HTTPException, QakeAPIException
from ..middleware.base import BaseMiddleware
from ..utils.status import status


class QakeAPI(APIRouter):
    """Main QakeAPI application class"""

    def __init__(
        self,
        debug: bool = False,
        title: str = "QakeAPI Application",
        description: str = "",
        version: str = "0.1.0",
        openapi_url: Optional[str] = "/openapi.json",
        docs_url: Optional[str] = "/docs",
        redoc_url: Optional[str] = "/redoc",
        middleware: Optional[Sequence[BaseMiddleware]] = None,
        exception_handlers: Optional[Dict[Union[int, type], Callable]] = None,
        on_startup: Optional[Sequence[Callable]] = None,
        on_shutdown: Optional[Sequence[Callable]] = None,
    ) -> None:
        super().__init__()

        self.debug = debug
        self.title = title
        self.description = description
        self.version = version
        self.openapi_url = openapi_url
        self.docs_url = docs_url
        self.redoc_url = redoc_url

        # Middleware
        self.middleware_stack: List[BaseMiddleware] = list(middleware or [])

        # Exception handlers
        # Order matters: more specific handlers should be checked first
        self.exception_handlers: Dict[Union[int, type], Callable] = {}
        # Add custom handlers first (they are more specific)
        if exception_handlers:
            self.exception_handlers.update(exception_handlers)
        # Then add default handlers
        self.exception_handlers.setdefault(HTTPException, self._http_exception_handler)
        self.exception_handlers.setdefault(
            QakeAPIException, self._qakeapi_exception_handler
        )
        self.exception_handlers.setdefault(Exception, self._generic_exception_handler)

        # Lifecycle events
        self.on_startup_handlers: List[Callable] = list(on_startup or [])
        self.on_shutdown_handlers: List[Callable] = list(on_shutdown or [])

        # Logger
        self.logger = logging.getLogger("qakeapi")
        if debug:
            self.logger.setLevel(logging.DEBUG)

        # Добаinляем inстроенные routeы
        self._add_builtin_routes()

    def _add_builtin_routes(self) -> None:
        """Добаinandть inстроенные routeы"""
        if self.openapi_url:

            @self.get(self.openapi_url, include_in_schema=False)
            async def openapi():
                return self.openapi()

        if self.docs_url:

            @self.get(self.docs_url, include_in_schema=False)
            async def swagger_ui():
                return self._get_swagger_ui_html()

        if self.redoc_url:

            @self.get(self.redoc_url, include_in_schema=False)
            async def redoc():
                return self._get_redoc_html()

    def add_middleware(self, middleware: BaseMiddleware) -> None:
        """Добаinandть middleware"""
        self.middleware_stack.append(middleware)

    def add_exception_handler(
        self,
        exc_class_or_status_code: Union[int, type],
        handler: Callable,
    ) -> None:
        """Добаinandть handler andсключенandй"""
        self.exception_handlers[exc_class_or_status_code] = handler

    def exception_handler(
        self,
        exc_class_or_status_code: Union[int, type],
    ) -> Callable:
        """Декоратор for добаinленandя handlerа andсключенandй"""

        def decorator(func: Callable) -> Callable:
            self.add_exception_handler(exc_class_or_status_code, func)
            return func

        return decorator

    def on_event(self, event_type: str) -> Callable:
        """Декоратор for соleastтandй жandзnotнного цandкла"""

        def decorator(func: Callable) -> Callable:
            if event_type == "startup":
                self.on_startup_handlers.append(func)
            elif event_type == "shutdown":
                self.on_shutdown_handlers.append(func)
            return func

        return decorator

    async def _http_exception_handler(
        self, request: Request, exc: HTTPException
    ) -> Response:
        """Обработчandк HTTP andсключенandй"""
        if isinstance(exc.detail, dict):
            return JSONResponse(
                content={"detail": exc.detail},
                status_code=exc.status_code,
                headers=exc.headers,
            )
        else:
            return JSONResponse(
                content={"detail": exc.detail},
                status_code=exc.status_code,
                headers=exc.headers,
            )

    async def _qakeapi_exception_handler(
        self, request: Request, exc: QakeAPIException
    ) -> Response:
        """Обработчandк QakeAPI andсключенandй"""
        return JSONResponse(
            content={"detail": exc.message},
            status_code=status.INTERNAL_SERVER_ERROR,
        )

    async def _generic_exception_handler(
        self, request: Request, exc: Exception
    ) -> Response:
        """Обработчandк общandх andсключенandй"""
        if self.debug:
            # В режandме отладкand показыinаем полную andнформацandю об ошandбке
            return JSONResponse(
                content={
                    "detail": "Internal Server Error",
                    "error": str(exc),
                    "traceback": traceback.format_exc().split("\n"),
                },
                status_code=status.INTERNAL_SERVER_ERROR,
            )
        else:
            return JSONResponse(
                content={"detail": "Internal Server Error"},
                status_code=status.INTERNAL_SERVER_ERROR,
            )

    async def _handle_exception(self, request: Request, exc: Exception) -> Response:
        """Обработать andсключенandе"""
        # Ищем подходящandй handler
        handler = None

        # Сначала andщем точное соinпаденandе по typeу andсключенandя (включая подклассы)
        # Проверяем в обратном порядке, чтобы более специфичные обработчики имели приоритет
        exc_type_chain = type(exc).__mro__  # Method Resolution Order
        for exc_type in exc_type_chain:
            if exc_type in self.exception_handlers:
                handler = self.exception_handlers[exc_type]
                break

        # Еслand это HTTP andсключенandе, andщем по codeу statusа
        if handler is None and isinstance(exc, HTTPException):
            handler = self.exception_handlers.get(exc.status_code)

        # Используем общandй handler, if not found спецandфandческandй
        if handler is None:
            handler = self.exception_handlers.get(Exception)

        if handler:
            try:
                if hasattr(handler, "__call__"):
                    result = handler(request, exc)
                    if hasattr(result, "__await__"):
                        return await result
                    return result
            except Exception as handler_exc:
                self.logger.error(f"Exception in exception handler: {handler_exc}")

        # Fallback handler
        return JSONResponse(
            content={"detail": "Internal Server Error"},
            status_code=status.INTERNAL_SERVER_ERROR,
        )

    async def _apply_middleware(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Прandменandть middleware"""
        if not self.middleware_stack:
            return await call_next(request)

        # Создаем цепочку middleware
        current_call_next = call_next

        # Прandменяем middleware in обратном порядке
        for middleware in reversed(self.middleware_stack):
            current_call_next = middleware.create_wrapper(current_call_next)

        return await current_call_next(request)

    async def _startup(self) -> None:
        """Выполнandть startup handlerand"""
        for handler in self.on_startup_handlers:
            try:
                if hasattr(handler, "__call__"):
                    result = handler()
                    if hasattr(result, "__await__"):
                        await result
            except Exception as e:
                self.logger.error(f"Error in startup handler: {e}")
                if self.debug:
                    raise

    async def _shutdown(self) -> None:
        """Выполнandть shutdown handlerand"""
        for handler in self.on_shutdown_handlers:
            try:
                if hasattr(handler, "__call__"):
                    result = handler()
                    if hasattr(result, "__await__"):
                        await result
            except Exception as e:
                self.logger.error(f"Error in shutdown handler: {e}")

    def openapi(self) -> Dict[str, Any]:
        """Геnotрandроinать OpenAPI схему"""
        import inspect

        # Базоinая OpenAPI схема
        openapi_schema = {
            "openapi": "3.0.2",
            "info": {
                "title": self.title,
                "description": self.description,
                "version": self.version,
            },
            "paths": {},
            "components": {
                "schemas": {},
            },
        }

        # Добаinляем путand andз routeоin
        for route in self.routes:
            if not route.include_in_schema or route.route_type != RouteType.HTTP:
                continue

            path_item = openapi_schema["paths"].setdefault(route.path, {})

            for method in route.methods:
                method_lower = method.lower()
                if method_lower in [
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "options",
                    "head",
                ]:
                    operation = {
                        "summary": route.name or f"{method_lower}_{route.path}",
                        "operationId": f"{method_lower}_{route.name or route.path.replace('/', '_')}",
                        "parameters": [],
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {"schema": {}}},
                            },
                            "422": {"description": "Validation Error"},
                        },
                    }

                    # Аналandзandруем params функцandand
                    if route.handler and callable(route.handler):
                        try:
                            sig = inspect.signature(route.handler)
                            for param_name, param in sig.parameters.items():
                                if param_name in ["request", "self"]:
                                    continue

                                # Параметры путand
                                if f"{{{param_name}}}" in route.path:
                                    operation["parameters"].append(
                                        {
                                            "name": param_name,
                                            "in": "path",
                                            "required": True,
                                            "schema": {"type": "string"},
                                        }
                                    )
                                # Query params
                                else:
                                    required = param.default == inspect.Parameter.empty
                                    param_schema = {"type": "string"}

                                    # Определяем type по аннотацandand
                                    if param.annotation != inspect.Parameter.empty:
                                        if param.annotation == int:
                                            param_schema = {"type": "integer"}
                                        elif param.annotation == float:
                                            param_schema = {"type": "number"}
                                        elif param.annotation == bool:
                                            param_schema = {"type": "boolean"}

                                    # Добаinляем значенandе по умолчанandю if есть
                                    if param.default != inspect.Parameter.empty:
                                        param_schema["default"] = param.default

                                    operation["parameters"].append(
                                        {
                                            "name": param_name,
                                            "in": "query",
                                            "required": required,
                                            "schema": param_schema,
                                        }
                                    )
                        except Exception as e:
                            # Отладочная andнформацandя
                            if self.debug:
                                print(
                                    f"Error analyzing parameters for {route.path}: {e}"
                                )
                            pass

                    # Добаinляем requestBody for POST/PUT/PATCH
                    if method_lower in ["post", "put", "patch"]:
                        operation["requestBody"] = {
                            "content": {
                                "application/json": {"schema": {"type": "object"}}
                            },
                            "required": True,
                        }

                    path_item[method_lower] = operation

        return openapi_schema

    def _get_swagger_ui_html(self) -> Response:
        """Получandть HTML for Swagger UI"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>{self.title} - Swagger UI</title>
            <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.18.2/swagger-ui.css" />
            <style>
                html {{
                    box-sizing: border-box;
                    overflow: -moz-scrollbars-vertical;
                    overflow-y: scroll;
                }}
                *, *:before, *:after {{
                    box-sizing: inherit;
                }}
                body {{
                    margin: 0;
                    background: #fafafa;
                }}
            </style>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@4.18.2/swagger-ui-bundle.js" charset="UTF-8"></script>
            <script src="https://unpkg.com/swagger-ui-dist@4.18.2/swagger-ui-standalone-preset.js" charset="UTF-8"></script>
            <script>
                window.onload = function() {{
                    const ui = SwaggerUIBundle({{
                        url: '{self.openapi_url}',
                        dom_id: '#swagger-ui',
                        deepLinking: true,
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIStandalonePreset
                        ],
                        plugins: [
                            SwaggerUIBundle.plugins.DownloadUrl
                        ],
                        layout: "StandaloneLayout",
                        validatorUrl: null,
                        tryItOutEnabled: true,
                        supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
                        onComplete: function() {{
                            console.log('Swagger UI loaded successfully');
                        }},
                        onFailure: function(error) {{
                            console.error('Swagger UI failed to load:', error);
                        }}
                    }});
                }};
            </script>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")

    def _get_redoc_html(self) -> Response:
        """Получandть HTML for ReDoc"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.title} - ReDoc</title>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                }}
            </style>
        </head>
        <body>
            <redoc spec-url='{self.openapi_url}'></redoc>
            <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")

    async def __call__(
        self, scope: Dict[str, Any], receive: callable, send: callable
    ) -> None:
        """ASGI andнтерфейс"""
        if scope["type"] == "lifespan":
            # Обработка соleastтandй жandзnotнного цandкла
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    try:
                        await self._startup()
                        await send({"type": "lifespan.startup.complete"})
                    except Exception as e:
                        await send(
                            {
                                "type": "lifespan.startup.failed",
                                "message": str(e),
                            }
                        )
                elif message["type"] == "lifespan.shutdown":
                    try:
                        await self._shutdown()
                        await send({"type": "lifespan.shutdown.complete"})
                    except Exception as e:
                        await send(
                            {
                                "type": "lifespan.shutdown.failed",
                                "message": str(e),
                            }
                        )
                    break  # Выходandм после shutdown
                elif message["type"] == "lifespan.disconnect":
                    break  # Выходandм прand disconnect

        elif scope["type"] == "http":
            # HTTP request
            request = Request(scope, receive)

            try:
                # Прandменяем middleware and обрабатыinаем request
                async def call_next(req: Request) -> Response:
                    return await self.handle_request(req)

                response = await self._apply_middleware(request, call_next)

            except Exception as exc:
                response = await self._handle_exception(request, exc)

            # Отpermissionsляем response
            await response(scope, receive, send)

        elif scope["type"] == "websocket":
            # WebSocket соедandnotнandе
            websocket = WebSocket(scope, receive, send)

            try:
                await self.handle_websocket(websocket)
            except Exception as exc:
                self.logger.error(f"WebSocket error: {exc}")
                if not websocket._closed:
                    await websocket.close(code=1011, reason="Internal server error")
