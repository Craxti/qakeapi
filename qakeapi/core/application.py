"""
Main Application class for the framework.

This module provides the QakeAPI Application class that serves as the
main entry point for ASGI applications.
"""

import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional
from .router import Router, APIRouter
from .request import Request
from .response import Response, JSONResponse, HTMLResponse
from .exceptions import HTTPException, NotFound, MethodNotAllowed, BadRequest
from .middleware_core import BaseMiddleware, MiddlewareStack
from .dependencies import resolve_dependencies, Dependency
from .websocket import WebSocket
from .openapi import OpenAPIGenerator, generate_swagger_ui_html, generate_redoc_html


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
        
        # Exception handlers
        self.exception_handlers: Dict[type, Callable] = {}
        
        # State
        self.state: Dict[str, Any] = {}
        self._started = False
    
    def add_middleware(self, middleware_class: type, **kwargs) -> None:
        """
        Add middleware to the application.
        
        Args:
            middleware_class: Middleware class
            **kwargs: Middleware initialization arguments
        """
        middleware = middleware_class(**kwargs)
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
    
    def include_router(self, router: APIRouter) -> None:
        """
        Include API router.
        
        Args:
            router: APIRouter instance
        """
        # Copy routes from router
        for route in router.routes:
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
                    raise MethodNotAllowed(
                        f"Method {request.method} not allowed"
                    )
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
                                    converted_path_params[param_name] = param_value.lower() in ("true", "1", "yes", "on")
                                else:
                                    converted_path_params[param_name] = bool(param_value)
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
                                            raise BadRequest("Request body is required and cannot be empty")
                                        if "Invalid JSON" in str(e):
                                            raise BadRequest("Invalid JSON in request body")
                                        raise BadRequest(f"Invalid JSON format: {str(e)}")
                                    
                                    # If parsed body is empty dict, check if original body was empty
                                    if not body:
                                        body_bytes = await request.body()
                                        if not body_bytes or not body_bytes.strip():
                                            raise BadRequest("Request body is required and cannot be empty")
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
                                    raise BadRequest(f"Invalid request body: {error_msg}")
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
                            cleaned_response = self._clean_response_data(response.__dict__)
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
                response = JSONResponse(
                    {"detail": exc.detail},
                    status_code=exc.status_code,
                    headers=exc.headers,
                )
            else:
                response = JSONResponse(
                    {"detail": str(exc)},
                    status_code=500,
                )
            
            await response(scope, receive, send)
    
    async def __call__(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """
        ASGI application interface.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
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
    
    async def _shutdown(self) -> None:
        """Run shutdown handlers."""
        for handler in self.shutdown_handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler()
            else:
                handler()
    
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
