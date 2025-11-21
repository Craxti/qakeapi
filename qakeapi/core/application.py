"""
Main Application class for the framework.

This module provides the QakeAPI Application class that serves as the
main entry point for ASGI applications.
"""

import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional

from .dependencies import Dependency, resolve_dependencies
from .exceptions import BadRequest, HTTPException, MethodNotAllowed, NotFound
from .middleware_core import BaseMiddleware, MiddlewareStack
from .openapi import OpenAPIGenerator, generate_redoc_html, generate_swagger_ui_html
from .request import Request
from .response import HTMLResponse, JSONResponse
from .response import Response as ResponseOld
from .responses import JSONResponse as JSONResponseNew
from .responses import PlainTextResponse, Response
from .router import APIRouter, Router
from .websocket import WebSocket


class _RequestResponseMiddlewareAdapter(BaseMiddleware):
    """Adapter to convert request/call_next middleware to ASGI middleware."""

    def __init__(self, request_middleware: Any):
        """
        Initialize adapter.

        Args:
            request_middleware: Middleware with __call__(request, call_next) interface
        """
        super().__init__()
        self.request_middleware = request_middleware

    async def process_http(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """Process HTTP request through request/call_next middleware."""
        # Create Request object
        request = Request(scope, receive)

        # Store response data
        response_data = {"status": 200, "headers": [], "body": b""}
        response_complete = False
        response_started = False

        # Wrapper to capture ASGI response
        async def send_wrapper(message: Dict[str, Any]) -> None:
            nonlocal response_data, response_complete, response_started
            if message["type"] == "http.response.start":
                response_data["status"] = message.get("status", 200)
                response_data["headers"] = message.get("headers", [])
                response_started = True
            elif message["type"] == "http.response.body":
                response_data["body"] += message.get("body", b"")
                if not message.get("more_body", False):
                    response_complete = True

        # Create call_next function
        async def call_next(req: Request) -> Response:
            # Reset response data
            nonlocal response_data, response_complete, response_started
            response_data = {"status": 200, "headers": [], "body": b""}
            response_complete = False
            response_started = False

            # Process through app
            if self.app:
                await self.app(scope, receive, send_wrapper)

            # Wait for response to complete
            import asyncio

            max_wait = 10  # 10 seconds max wait
            waited = 0
            while not response_complete and waited < max_wait:
                await asyncio.sleep(0.01)
                waited += 0.01

            if not response_started:
                # No response was sent - create default response
                response_obj = JSONResponse({"detail": "No response"}, status_code=500)
                return response_obj

            # Convert ASGI response to Response object
            headers_list = response_data["headers"]
            headers = []
            for header in headers_list:
                if isinstance(header, (list, tuple)) and len(header) == 2:
                    headers.append((header[0], header[1]))

            # Convert headers to dict format if needed
            headers_dict = {}
            for header in headers_list:
                if isinstance(header, (list, tuple)) and len(header) == 2:
                    key = (
                        header[0].decode()
                        if isinstance(header[0], bytes)
                        else header[0]
                    )
                    value = (
                        header[1].decode()
                        if isinstance(header[1], bytes)
                        else header[1]
                    )
                    headers_dict[key.lower()] = value

            # Use Response from qakeapi/core/responses.py which is what middleware expects
            # Convert headers_list to list of tuples format
            headers_list_formatted = []
            for header in headers_list:
                if isinstance(header, (list, tuple)) and len(header) == 2:
                    headers_list_formatted.append((header[0], header[1]))

            # Try to parse as JSON, if successful use JSONResponse
            try:
                import json

                if response_data["body"]:
                    content = json.loads(response_data["body"].decode())
                    response_obj = JSONResponseNew(
                        content=content,
                        status_code=response_data["status"],
                        headers=headers_list_formatted
                        if headers_list_formatted
                        else None,
                    )
                else:
                    response_obj = Response(
                        content=None,
                        status_code=response_data["status"],
                        headers=headers_list_formatted
                        if headers_list_formatted
                        else None,
                    )
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON, use regular Response from responses.py
                response_obj = Response(
                    content=response_data["body"],
                    status_code=response_data["status"],
                    headers=headers_list_formatted if headers_list_formatted else None,
                )
            return response_obj

        # Call request middleware and handle exceptions
        try:
            response = await self.request_middleware(request, call_next)
            # Ensure response is a Response object from responses.py
            # Response from responses.py uses __call__(send) interface
            if hasattr(response, "__call__"):
                # Response has ASGI interface (takes send parameter)
                await response(send)
            else:
                # Fallback: create JSONResponseNew
                response = JSONResponseNew(
                    response if isinstance(response, dict) else {"data": response}
                )
                await response(send)
        except HTTPException as exc:
            # HTTP exceptions should be handled by _handle_request
            # But we're in middleware, so we need to handle them here
            # Create error response and send it
            headers_dict = {}
            if exc.headers:
                if isinstance(exc.headers, dict):
                    headers_dict = exc.headers
                else:
                    # Convert list to dict
                    for header in exc.headers:
                        if isinstance(header, (list, tuple)) and len(header) == 2:
                            key = (
                                header[0].decode()
                                if isinstance(header[0], bytes)
                                else header[0]
                            )
                            value = (
                                header[1].decode()
                                if isinstance(header[1], bytes)
                                else header[1]
                            )
                            headers_dict[key] = value
            # Convert headers_dict to list format for Response
            headers_list = []
            if headers_dict:
                headers_list = [
                    (k.encode(), v.encode() if isinstance(v, str) else v)
                    for k, v in headers_dict.items()
                ]

            error_response = JSONResponseNew(
                {"detail": exc.detail},
                status_code=exc.status_code,
                headers=headers_list if headers_list else None,
            )
            await error_response(send)
            return
        except Exception as exc:
            # Other exceptions - re-raise to be handled by _handle_request
            # But since we're in middleware stack, we need to handle them
            error_response = JSONResponseNew(
                {"detail": str(exc)},
                status_code=500,
            )
            await error_response(send)
            return


class QakeAPI:
    """
    Main application class.

    This is the core of the framework. It manages routes, middleware,
    and handles ASGI requests.
    """

    def __init__(
        self,
        title: str = "QakeAPI",
        version: str = "1.1.0",
        description: str = "",
        debug: bool = False,
    ):
        """
        Initialize application.

        Args:
            title: Application title
            version: Application version
            description: Application description
            debug: Debug mode
        """
        self.title = title
        self.version = version
        self.description = description
        self.debug = debug

        self.router = Router()
        self.websocket_routes: Dict[str, Callable] = {}
        self.middleware_stack = MiddlewareStack(self._handle_request)

        # OpenAPI settings
        self.openapi_url = "/openapi.json"
        self.docs_url = "/docs"
        self.redoc_url = "/redoc"
        self.openapi_generator = OpenAPIGenerator(
            title=title,
            version=version,
            description=description,
        )

        # Lifecycle events
        self.startup_handlers: List[Callable] = []
        self.shutdown_handlers: List[Callable] = []
        self.on_shutdown_handlers: List[Callable] = []  # Alias for shutdown_handlers

        # Exception handlers
        self.exception_handlers: Dict[type, Callable] = {}

        # State
        self.state: Dict[str, Any] = {}
        self._started = False

    def add_middleware(self, middleware_class: type = None, **kwargs) -> None:
        """
        Add middleware to the application.

        Args:
            middleware_class: Middleware class or instance
            **kwargs: Middleware initialization arguments (only used if middleware_class is a class)
        """
        # Handle both class and instance
        if isinstance(middleware_class, type):
            # It's a class, instantiate it
            middleware = middleware_class(**kwargs)
        else:
            # It's already an instance
            middleware = middleware_class

        # Check if middleware has request/call_next interface
        # If so, wrap it in an ASGI adapter
        if hasattr(middleware, "__call__"):
            try:
                sig = inspect.signature(middleware.__call__)
                params = list(sig.parameters.keys())
                # Check if it's request/call_next interface (2 params: request, call_next)
                # Exclude 'self' from params count
                non_self_params = [p for p in params if p != "self"]
                if (
                    len(non_self_params) >= 2
                    and "request" in params
                    and "call_next" in params
                ):
                    # Wrap in ASGI adapter
                    middleware = _RequestResponseMiddlewareAdapter(middleware)
            except (ValueError, TypeError):
                # If signature inspection fails, assume it's ASGI middleware
                pass

        self.middleware_stack.add(middleware)

    def on_event(self, event_type: str) -> Callable:
        """
        Decorator for lifecycle events.

        Args:
            event_type: Event type ("startup" or "shutdown")

        Returns:
            Decorator function
        """

        def decorator(handler: Callable) -> Callable:
            if event_type == "startup":
                self.startup_handlers.append(handler)
            elif event_type == "shutdown":
                self.shutdown_handlers.append(handler)
                self.on_shutdown_handlers.append(handler)  # Sync with alias
            return handler

        return decorator

    def exception_handler(self, exc_class: type) -> Callable:
        """
        Decorator for exception handlers.

        Args:
            exc_class: Exception class to handle

        Returns:
            Decorator function
        """

        def decorator(handler: Callable) -> Callable:
            self.exception_handlers[exc_class] = handler
            return handler

        return decorator

    def get(self, path: str, name: Optional[str] = None):
        """Decorator for GET routes."""
        return self.router.get(path, name)

    def post(self, path: str, name: Optional[str] = None):
        """Decorator for POST routes."""
        return self.router.post(path, name)

    def put(self, path: str, name: Optional[str] = None):
        """Decorator for PUT routes."""
        return self.router.put(path, name)

    def delete(self, path: str, name: Optional[str] = None):
        """Decorator for DELETE routes."""
        return self.router.delete(path, name)

    def patch(self, path: str, name: Optional[str] = None):
        """Decorator for PATCH routes."""
        return self.router.patch(path, name)

    def websocket(self, path: str):
        """
        Decorator for WebSocket routes.

        Args:
            path: WebSocket path

        Returns:
            Decorator function
        """

        def decorator(handler: Callable) -> Callable:
            self.websocket_routes[path] = handler
            return handler

        return decorator

    def include_router(self, router: APIRouter, prefix: str = "") -> None:
        """
        Include API router.

        Args:
            router: APIRouter instance
            prefix: Optional prefix for all routes
        """
        # Copy routes from router
        for route in router.routes:
            # Apply prefix if provided
            if prefix:
                route.path = prefix.rstrip("/") + "/" + route.path.lstrip("/")
            self.router.routes.append(route)
            for method in route.methods:
                self.router.route_map[method][route.path] = route

    async def _handle_request(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """
        Handle HTTP request.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            return

        # Handle OpenAPI endpoints
        path = scope.get("path", "/")

        if path == self.openapi_url:
            await self._handle_openapi(scope, receive, send)
            return

        if path == self.docs_url:
            await self._handle_swagger_ui(scope, receive, send)
            return

        if path == self.redoc_url:
            await self._handle_redoc(scope, receive, send)
            return

        request = None
        try:
            # Create request object
            request = Request(scope, receive)

            # Find route
            route_match = self.router.find_route(request.path, request.method)

            if not route_match:
                # Check if path exists with different method
                path_exists = False
                for route in self.router.routes:
                    if route.match(request.path):
                        path_exists = True
                        break

                if path_exists:
                    # Method not allowed
                    raise MethodNotAllowed(f"Method {request.method} not allowed")
                else:
                    # Route not found
                    raise NotFound(f"Route {request.path} not found")

            route, path_params = route_match
            request._path_params = path_params

            # Convert path params to correct types based on handler signature
            sig = inspect.signature(route.handler)
            converted_path_params = {}
            for param_name, param_value in path_params.items():
                if param_name in sig.parameters:
                    param = sig.parameters[param_name]
                    param_type = param.annotation
                    if param_type != inspect.Parameter.empty:
                        # Try to convert type
                        try:
                            if param_type == int:
                                converted_path_params[param_name] = int(param_value)
                            elif param_type == float:
                                converted_path_params[param_name] = float(param_value)
                            elif param_type == bool:
                                if isinstance(param_value, str):
                                    converted_path_params[
                                        param_name
                                    ] = param_value.lower() in (
                                        "true",
                                        "1",
                                        "yes",
                                        "on",
                                    )
                                else:
                                    converted_path_params[param_name] = bool(
                                        param_value
                                    )
                            else:
                                converted_path_params[param_name] = param_value
                        except (ValueError, TypeError):
                            converted_path_params[param_name] = param_value
                else:
                    converted_path_params[param_name] = param_value

            path_params = converted_path_params
            request._path_params = path_params

            # Get query params
            query_params = {}
            for key, values in request.query_params.items():
                query_params[key] = values[0] if values else None

            # Resolve dependencies
            dependencies = await resolve_dependencies(
                route.handler, request, path_params, query_params
            )

            # Call route handler
            handler = route.handler

            # Prepare handler arguments
            handler_kwargs = {}

            # Add path params
            handler_kwargs.update(path_params)

            # Add query params
            handler_kwargs.update(query_params)

            # Add dependencies
            handler_kwargs.update(dependencies)

            # Add request if handler expects it
            # Also handle BaseModel parameters (body models)
            sig = inspect.signature(handler)
            for param_name in sig.parameters:
                if param_name not in handler_kwargs:
                    param = sig.parameters[param_name]
                    param_type = param.annotation

                    # Check if it's Request
                    if param_type == Request or (
                        hasattr(param_type, "__name__")
                        and param_type.__name__ == "Request"
                    ):
                        handler_kwargs[param_name] = request
                    # Check if it's a BaseModel (body model)
                    elif param_type != inspect.Parameter.empty:
                        # Check if it's a BaseModel subclass by checking for _get_fields method
                        is_basemodel = False
                        if inspect.isclass(param_type):
                            # Check MRO for BaseModel
                            for base in param_type.__mro__:
                                if base != object and hasattr(base, "_get_fields"):
                                    is_basemodel = True
                                    break

                        if is_basemodel:
                            # Extract body and create model instance
                            # Only for methods that typically have body (POST, PUT, PATCH)
                            if request.method in ("POST", "PUT", "PATCH"):
                                try:
                                    # Try to parse JSON body
                                    try:
                                        body = await request.json()
                                    except ValueError as e:
                                        # JSON parsing error - check if body exists
                                        body_bytes = await request.body()
                                        if not body_bytes or not body_bytes.strip():
                                            raise BadRequest(
                                                "Request body is required and cannot be empty"
                                            )
                                        if "Invalid JSON" in str(e):
                                            raise BadRequest(
                                                "Invalid JSON in request body"
                                            )
                                        raise BadRequest(
                                            f"Invalid JSON format: {str(e)}"
                                        )

                                    # If parsed body is empty dict, check if original body was empty
                                    if not body:
                                        body_bytes = await request.body()
                                        if not body_bytes or not body_bytes.strip():
                                            raise BadRequest(
                                                "Request body is required and cannot be empty"
                                            )
                                        # Body was sent but parsed as empty - try to create model anyway
                                        # This will trigger validation errors for required fields

                                    # Try to create model with body data
                                    handler_kwargs[param_name] = param_type(**body)
                                except BadRequest:
                                    # Re-raise BadRequest as is
                                    raise
                                except Exception as e:
                                    # Other errors (validation errors from model)
                                    error_msg = str(e)
                                    if "Required field missing" in error_msg:
                                        raise BadRequest(error_msg)
                                    raise BadRequest(
                                        f"Invalid request body: {error_msg}"
                                    )
                            else:
                                # For GET/DELETE, try to create with defaults
                                handler_kwargs[param_name] = param_type()

            # Check if handler is async
            if asyncio.iscoroutinefunction(handler):
                response = await handler(**handler_kwargs)
            else:
                response = handler(**handler_kwargs)

            # Convert response to Response object if needed
            if not isinstance(response, Response):
                # Clean response data - remove any Dependency objects
                if isinstance(response, dict):
                    cleaned_response = self._clean_response_data(response)
                    response = JSONResponse(cleaned_response)
                elif isinstance(response, str):
                    response = JSONResponse({"message": response})
                else:
                    # Try to convert to dict and clean
                    try:
                        if hasattr(response, "__dict__"):
                            cleaned_response = self._clean_response_data(
                                response.__dict__
                            )
                            response = JSONResponse(cleaned_response)
                        else:
                            response = JSONResponse({"data": str(response)})
                    except Exception:
                        response = JSONResponse({"data": str(response)})

            # Send response
            await response(scope, receive, send)

        except HTTPException as exc:
            # Handle HTTP exceptions
            await self._handle_exception(exc, scope, receive, send, request)
        except ValueError as exc:
            # Handle ValueError (e.g., invalid JSON)
            error_msg = str(exc)
            if "Invalid JSON" in error_msg:
                # Convert JSON parsing errors to BadRequest
                await self._handle_exception(
                    BadRequest("Invalid JSON format"), scope, receive, send, request
                )
            else:
                # Other ValueError - convert to BadRequest
                await self._handle_exception(
                    BadRequest(str(exc)), scope, receive, send, request
                )
        except Exception as exc:
            # Handle other exceptions
            if self.debug:
                # In debug mode, raise to see traceback
                raise
            await self._handle_exception(
                HTTPException(500, str(exc)), scope, receive, send, request
            )

    async def _handle_exception(
        self,
        exc: Exception,
        scope: Dict[str, Any],
        receive: Any,
        send: Any,
        request: Optional[Request] = None,
    ) -> None:
        """
        Handle exception by finding appropriate handler.

        Args:
            exc: Exception instance
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
            request: Request object (if available)
        """
        # Find exception handler
        handler = None
        exc_type = type(exc)

        # Try exact match
        if exc_type in self.exception_handlers:
            handler = self.exception_handlers[exc_type]
        else:
            # Try base classes
            for base in exc_type.__mro__:
                if base in self.exception_handlers:
                    handler = self.exception_handlers[base]
                    break

        if handler:
            # Use existing request if available, otherwise create new one
            if request is None:
                request = Request(scope, receive)

            # Call custom handler with correct signature
            sig = inspect.signature(handler)
            params = {}

            # Check handler signature
            param_names = list(sig.parameters.keys())
            if len(param_names) >= 1:
                # First parameter should be Request
                params[param_names[0]] = request
            if len(param_names) >= 2:
                # Second parameter should be exception
                params[param_names[1]] = exc

            if asyncio.iscoroutinefunction(handler):
                response = await handler(**params)
            else:
                response = handler(**params)

            if not isinstance(response, Response):
                response = JSONResponse(response)

            await response(scope, receive, send)
        else:
            # Default handler
            if isinstance(exc, HTTPException):
                # Преобразуем headers из dict в list кортежей если нужно
                headers_list = []
                if exc.headers:
                    if isinstance(exc.headers, dict):
                        for k, v in exc.headers.items():
                            if isinstance(v, str):
                                headers_list.append((k.encode(), v.encode()))
                            else:
                                headers_list.append(
                                    (
                                        k.encode() if isinstance(k, bytes) else k,
                                        v if isinstance(v, bytes) else str(v).encode(),
                                    )
                                )
                    else:
                        headers_list = exc.headers
                response = JSONResponse(
                    {"detail": exc.detail},
                    status_code=exc.status_code,
                    headers=headers_list,
                )
            else:
                response = JSONResponse(
                    {"detail": str(exc)},
                    status_code=500,
                )

            await response(scope, receive, send)

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        """
        ASGI application interface.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Handle lifespan events
        if scope["type"] == "lifespan":
            await self._handle_lifespan(scope, receive, send)
            return

        # Run startup handlers on first request
        if not self._started:
            await self._startup()
            self._started = True

        # Handle WebSocket connections
        if scope["type"] == "websocket":
            await self._handle_websocket(scope, receive, send)
        else:
            # Process through middleware stack
            await self.middleware_stack(scope, receive, send)

    async def _startup(self) -> None:
        """Run startup handlers."""
        for handler in self.startup_handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler()
            else:
                handler()

    async def _handle_websocket(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """
        Handle WebSocket connection.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        path = scope.get("path", "/")

        # Find WebSocket route
        handler = self.websocket_routes.get(path)

        if not handler:
            # Reject connection
            await send({"type": "websocket.close", "code": 404})
            return

        # Create WebSocket object
        websocket = WebSocket(scope, receive, send)

        try:
            # Call handler
            if asyncio.iscoroutinefunction(handler):
                await handler(websocket)
            else:
                handler(websocket)
        except Exception as exc:
            if self.debug:
                raise
            # Close connection on error
            if websocket.state.value != "disconnected":
                await websocket.close(code=1011, reason=str(exc))

    async def _handle_openapi(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """Handle OpenAPI schema request."""
        schema = self.openapi_generator.generate_schema(self.router)
        response = JSONResponse(schema)
        await response(scope, receive, send)

    async def _handle_swagger_ui(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """Handle Swagger UI request."""
        html = generate_swagger_ui_html(self.openapi_url)
        response = HTMLResponse(html)
        await response(scope, receive, send)

    async def _handle_redoc(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """Handle ReDoc request."""
        html = generate_redoc_html(self.openapi_url)
        response = HTMLResponse(html)
        await response(scope, receive, send)

    async def _startup(self) -> None:
        """Run startup handlers."""
        for handler in self.startup_handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler()
            else:
                handler()

    async def _apply_middleware(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Apply middleware to request.

        Args:
            request: Request object
            call_next: Next handler in chain

        Returns:
            Response object
        """

        # Create a simple middleware chain executor
        async def execute_middleware(middleware_list, index, req):
            if index >= len(middleware_list):
                return await call_next(req)

            middleware = middleware_list[index]

            # Check if middleware has request/call_next interface
            if hasattr(middleware, "__call__"):
                try:
                    sig = inspect.signature(middleware.__call__)
                    params = list(sig.parameters.keys())
                    non_self_params = [p for p in params if p != "self"]
                    if (
                        len(non_self_params) >= 2
                        and "request" in params
                        and "call_next" in params
                    ):
                        # Request/call_next interface
                        async def next_handler(r):
                            return await execute_middleware(
                                middleware_list, index + 1, r
                            )

                        return await middleware(req, next_handler)
                except (ValueError, TypeError):
                    pass

            # Default: continue to next middleware
            return await execute_middleware(middleware_list, index + 1, req)

        # Get request/call_next middleware from stack
        request_middleware = []
        for mw in self.middleware_stack.middleware:
            if hasattr(mw, "__call__"):
                try:
                    sig = inspect.signature(mw.__call__)
                    params = list(sig.parameters.keys())
                    non_self_params = [p for p in params if p != "self"]
                    if (
                        len(non_self_params) >= 2
                        and "request" in params
                        and "call_next" in params
                    ):
                        request_middleware.append(mw)
                except (ValueError, TypeError):
                    pass

        return await execute_middleware(request_middleware, 0, request)

    async def _shutdown(self) -> None:
        """Run shutdown handlers."""
        for handler in self.shutdown_handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler()
            else:
                handler()

    async def _handle_lifespan(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """
        Handle lifespan events (startup/shutdown).

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        message = await receive()

        while True:
            if message["type"] == "lifespan.startup":
                # Run startup handlers
                try:
                    await self._startup()
                    await send({"type": "lifespan.startup.complete"})
                except Exception as exc:
                    await send({"type": "lifespan.startup.failed", "message": str(exc)})
                    return
            elif message["type"] == "lifespan.shutdown":
                # Run shutdown handlers
                try:
                    await self._shutdown()
                    await send({"type": "lifespan.shutdown.complete"})
                except Exception as exc:
                    await send(
                        {"type": "lifespan.shutdown.failed", "message": str(exc)}
                    )
                    return
            elif message["type"] == "lifespan.disconnect":
                return

            message = await receive()

    def openapi(self) -> Dict[str, Any]:
        """
        Generate OpenAPI schema.

        Returns:
            OpenAPI schema dictionary
        """
        return self.openapi_generator.generate_schema(self.router)

    def _clean_response_data(self, data: Any) -> Any:
        """
        Clean response data by removing non-serializable objects.

        Args:
            data: Data to clean

        Returns:
            Cleaned data
        """
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                # Skip Dependency objects
                if isinstance(value, Dependency):
                    continue
                cleaned[key] = self._clean_response_data(value)
            return cleaned
        elif isinstance(data, (list, tuple)):
            cleaned = []
            for item in data:
                if not isinstance(item, Dependency):
                    cleaned.append(self._clean_response_data(item))
            return cleaned if isinstance(data, list) else tuple(cleaned)
        else:
            return data
