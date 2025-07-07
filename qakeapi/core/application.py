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
from .routing import HTTPRouter, WebSocketRouter, MiddlewareManager
from .websockets import WebSocketConnection, WebSocketState
from ..api.versioning import APIVersionManager, PathVersionStrategy
from ..api.deprecation import DeprecationManager

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Application:
    """Main application class with new routing architecture."""

    def __init__(self, title: str = "QakeAPI", version: str = "1.0.3", description: str = ""):
        self.title = title
        self.version = version
        self.description = description
        
        # Initialize routers
        self.http_router = HTTPRouter()
        self.ws_router = WebSocketRouter()
        self.middleware_manager = MiddlewareManager()
        
        # Initialize other components
        self.background_tasks = BackgroundTaskManager()
        self.dependency_container = DependencyContainer()
        self.openapi_generator = OpenAPIGenerator(
            OpenAPIInfo(title=title, version=version, description=description)
        )
        
        # Initialize API versioning and deprecation
        self.version_manager = APIVersionManager(
            PathVersionStrategy(["v1", "v2"], "v1")
        )
        self.deprecation_manager = DeprecationManager()
        
        # Startup and shutdown handlers
        self.startup_handlers: List[Callable] = []
        self.shutdown_handlers: List[Callable] = []
        
        # Add default routes
        self.http_router.add_route("/docs", self.swagger_ui, ["GET"])
        self.http_router.add_route("/openapi.json", self.openapi_schema, ["GET"])
        self.http_router.add_route("/api/versions", self.api_versions, ["GET"])
        self.http_router.add_route("/api/changelog", self.api_changelog, ["GET"])
        self.http_router.add_route("/api/deprecations", self.api_deprecations, ["GET"])
        
        self.asgi_mounts = {}  # path -> ASGI app
        
        logger.debug("Application initialized")

    def route(self, path: str, methods: List[str] = None, name: Optional[str] = None):
        """Route decorator for HTTP endpoints."""
        return self.http_router.route(path, methods, name)

    def websocket(self, path: str, name: Optional[str] = None):
        """Route decorator for WebSocket endpoints."""
        return self.ws_router.websocket(path, name)

    def middleware(self):
        """Middleware decorator."""
        return self.middleware_manager.decorator()

    def on_startup(self, handler: Callable):
        """Register startup handler."""
        self.startup_handlers.append(handler)
        return handler

    def on_shutdown(self, handler: Callable):
        """Register shutdown handler."""
        self.shutdown_handlers.append(handler)
        return handler

    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        """ASGI interface."""
        # Проверяем, есть ли монтированное ASGI-приложение для пути
        if scope["type"] == "http":
            path = scope.get("path", "")
            for prefix, asgi_app in self.asgi_mounts.items():
                if path.startswith(prefix):
                    await asgi_app(scope, receive, send)
                    return
            await self.handle_http(scope, receive, send)
        elif scope["type"] == "websocket":
            await self.handle_websocket(scope, receive, send)
        elif scope["type"] == "lifespan":
            await self.handle_lifespan(scope, receive, send)

    async def handle_http(
        self, scope: Dict[str, Any], receive: Callable, send: Callable
    ) -> None:
        """Handle HTTP request."""
        try:
            # Get request body
            body = b""
            more_body = True
            while more_body:
                message = await receive()
                body += message.get("body", b"")
                more_body = message.get("more_body", False)

            # Create Request object
            request = Request(scope, body)
            request.dependency_container = self.dependency_container
            request.scope["dependency_container"] = self.dependency_container
            
            logger.debug(f"Handling HTTP request: {request.method} {request.path}")

            # Handle request using HTTP router
            response = await self.http_router.handle_request(request)
            
            # Send response
            if isinstance(response, Response):
                await response(send)
            else:
                await Response.json(response)(send)

        except Exception as e:
            logger.error(f"Error handling HTTP request: {str(e)}", exc_info=True)
            response = Response.json({"detail": "Internal Server Error"}, status_code=500)
            await response(send)

    async def handle_websocket(
        self, scope: Dict[str, Any], receive: Callable, send: Callable
    ) -> None:
        """Handle WebSocket connection."""
        try:
            websocket = WebSocketConnection(scope, receive, send)
            logger.debug(f"Handling WebSocket connection: {websocket.path}")
            
            # Handle WebSocket using WebSocket router
            await self.ws_router.handle_request(websocket)
            
        except Exception as e:
            logger.error(f"Error handling WebSocket: {str(e)}", exc_info=True)
            await send({"type": "websocket.close", "code": 1011})

    async def handle_lifespan(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        """Handle lifespan events."""
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
        """Application startup."""
        logger.debug("Starting application")
        for handler in self.startup_handlers:
            await handler()

    async def shutdown(self) -> None:
        """Application shutdown."""
        logger.debug("Shutting down application")
        for handler in self.shutdown_handlers:
            await handler()
        await self.dependency_container.cleanup_all()

    async def add_background_task(
        self,
        func: Callable,
        *args: Any,
        task_id: Optional[str] = None,
        timeout: Optional[float] = None,
        retry_count: int = 0,
        **kwargs: Any,
    ) -> str:
        """Add background task."""
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
        """Get background task status."""
        return self.background_tasks.get_task_status(task_id)

    async def cancel_background_task(self, task_id: str) -> bool:
        """Cancel background task."""
        return await self.background_tasks.cancel_task(task_id)

    # HTTP method decorators
    def get(self, path: str, **kwargs):
        """GET route decorator."""
        def decorator(handler: Callable):
            handler.openapi_metadata = {
                "summary": kwargs.get("summary", ""),
                "description": kwargs.get("description", ""),
                "response_model": kwargs.get("response_model"),
                "tags": kwargs.get("tags", []),
            }
            self.http_router.add_route(path, handler, ["GET"])
            return handler
        return decorator

    def post(self, path: str, **kwargs):
        """POST route decorator."""
        def decorator(handler: Callable):
            handler.openapi_metadata = {
                "summary": kwargs.get("summary", ""),
                "description": kwargs.get("description", ""),
                "request_model": kwargs.get("request_model"),
                "response_model": kwargs.get("response_model"),
                "tags": kwargs.get("tags", []),
            }
            self.http_router.add_route(path, handler, ["POST"])
            return handler
        return decorator

    def put(self, path: str, **kwargs):
        """PUT route decorator."""
        def decorator(handler: Callable):
            self.http_router.add_route(path, handler, ["PUT"])
            return handler
        return decorator

    def delete(self, path: str, **kwargs):
        """DELETE route decorator."""
        def decorator(handler: Callable):
            self.http_router.add_route(path, handler, ["DELETE"])
            return handler
        return decorator

    def patch(self, path: str, **kwargs):
        """PATCH route decorator."""
        def decorator(handler: Callable):
            self.http_router.add_route(path, handler, ["PATCH"])
            return handler
        return decorator

    def options(self, path: str, **kwargs):
        """OPTIONS route decorator."""
        def decorator(handler: Callable):
            self.http_router.add_route(path, handler, ["OPTIONS"])
            return handler
        return decorator

    def api_route(self, path: str, methods: List[str] = None, **kwargs):
        """API route decorator."""
        if methods is None:
            methods = ["GET"]
        methods = [m.upper() for m in methods]

        def decorator(handler: Callable):
            self.http_router.add_route(path, handler, methods)
            return handler
        return decorator

    async def swagger_ui(self, request: Request):
        """Serve Swagger UI."""
        return Response.html(get_swagger_ui_html("/openapi.json", self.title))

    async def api_versions(self, request: Request):
        """Get API version information."""
        return {
            "current_version": self.version,
            "supported_versions": self.version_manager.get_supported_versions(),
            "default_version": self.version_manager.strategy.get_default_version(),
            "version_info": {
                version: {
                    "deprecated": self.version_manager.is_version_deprecated(version),
                    "info": self.version_manager.get_version_info(version)
                }
                for version in self.version_manager.get_supported_versions()
            }
        }
    
    async def api_changelog(self, request: Request):
        """Get API changelog."""
        return self.version_manager.generate_changelog()
    
    async def api_deprecations(self, request: Request):
        """Get deprecation information."""
        return {
            "active_deprecations": [
                {
                    "feature": dep.feature,
                    "version": dep.version,
                    "deprecation_date": dep.deprecation_date.isoformat(),
                    "sunset_date": dep.sunset_date.isoformat() if dep.sunset_date else None,
                    "replacement": dep.replacement,
                    "migration_guide": dep.migration_guide
                }
                for dep in self.deprecation_manager.get_active_deprecations()
            ],
            "sunset_features": self.deprecation_manager.get_sunset_features()
        }
    
    async def openapi_schema(self, request: Request):
        """Generate and return OpenAPI schema."""
        logger.debug("Generating OpenAPI schema")
        schema = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description,
            },
            "paths": {},
        }

        # Add paths from HTTP router
        for route in self.http_router.routes:
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
                        path_data["parameters"].append({
                            "name": param_name,
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        })

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

        logger.debug("OpenAPI schema generated successfully")
        return Response(
            content=json.dumps(schema, indent=2),
            status_code=200,
            headers=[
                (b"content-type", b"application/json"),
                (b"access-control-allow-origin", b"*"),
                (b"cache-control", b"no-cache"),
            ],
        )

    def add_middleware(self, middleware):
        """Add middleware to the application (function or class)."""
        self.middleware_manager.add(middleware)

    def mount(self, path: str, asgi_app):
        """Монтирует ASGI-приложение на указанный путь."""
        self.asgi_mounts[path.rstrip("/")] = asgi_app
