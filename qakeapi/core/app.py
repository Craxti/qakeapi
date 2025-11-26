"""
Main Application class - QakeAPI.

This is the core of the framework, providing:
- Hybrid sync/async execution
- Smart routing
- Reactive events
- Parallel dependencies
- Pipeline composition
"""

import asyncio
import atexit
import inspect
import json
from typing import Any, Callable, Dict, List, Optional

from .background import BackgroundTaskManager, add_background_task
from .caching import get_cache, generate_cache_key
from .dependencies import Dependency, Depends, resolve_dependency_values
from .exceptions import HTTPException, ValidationError as HTTPValidationError
from .hybrid import hybrid_executor, run_hybrid, shutdown_executor
from .logging import get_logger, configure_logging
from .middleware import BaseMiddleware, MiddlewareStack, CORSMiddleware, LoggingMiddleware
from .openapi import OpenAPIGenerator, SWAGGER_UI_HTML
from .rate_limit import get_rate_limiter
from .reactive import EventBus, emit
from .request import Request
from .response import HTMLResponse, JSONResponse, Response
from .router import Router, Route
from .validation import ValidationError, validate_model, validate_path_param, validate_query_param, validate_request_body
from .websocket import WebSocket, WebSocketRoute
from .files import FileUpload


class QakeAPI:
    """
    Main QakeAPI application class.
    
    Revolutionary web framework with hybrid sync/async support,
    reactive routing, and parallel dependency resolution.
    """
    
    def __init__(
        self,
        title: str = "QakeAPI",
        version: str = "1.2.0",
        description: str = "",
        debug: bool = False,
    ):
        """
        Initialize QakeAPI application.
        
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
        
        # Initialize logger
        log_level = "DEBUG" if debug else "INFO"
        self.logger = get_logger(name="qakeapi", level=log_level)
        
        self.router = Router()
        self.event_bus = EventBus()
        self.openapi_generator = OpenAPIGenerator(title, version, description)
        self.background_manager = BackgroundTaskManager()
        self.middleware_stack: Optional[MiddlewareStack] = None
        self._middleware: List[BaseMiddleware] = []
        self._websocket_routes: List[WebSocketRoute] = []
        self._startup_handlers: List[Callable[..., Any]] = []
        self._shutdown_handlers: List[Callable[..., Any]] = []
        self._started = False
        
        # Automatically register executor shutdown handler
        self.on_shutdown(shutdown_executor)
        
        # Register atexit handler as fallback for executor shutdown
        atexit.register(shutdown_executor, wait=False)
        
        # OpenAPI endpoints
        self.docs_url = "/docs"
        self.openapi_url = "/openapi.json"
    
    def websocket(self, path: str):
        """
        WebSocket route decorator.
        
        Args:
            path: WebSocket path pattern
            
        Example:
            ```python
            @app.websocket("/ws")
            async def websocket_handler(websocket: WebSocket):
                await websocket.accept()
                await websocket.send_text("Hello!")
            ```
        """
        def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
            route = WebSocketRoute(path, handler)
            self._websocket_routes.append(route)
            return handler
        
        return decorator
    
    def add_middleware(self, middleware: BaseMiddleware) -> None:
        """
        Add middleware to application.
        
        Args:
            middleware: Middleware instance
            
        Example:
            ```python
            from qakeapi.core.middleware import CORSMiddleware, LoggingMiddleware
            
            app.add_middleware(LoggingMiddleware())
            app.add_middleware(CORSMiddleware(allow_origins=["*"]))
            ```
        """
        self._middleware.append(middleware)
    
    # Reactive Events
    
    def react(self, event_name: str):
        """
        Reactive decorator - register function to react to events.
        
        Args:
            event_name: Event name to react to
            
        Example:
            ```python
            @app.react("user:created")
            async def on_user_created(event):
                print(f"User created: {event.data}")
            ```
        """
        def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
            self.event_bus.subscribe(event_name, handler)
            return handler
        
        return decorator
    
    async def emit(self, event_name: str, data: Any = None) -> None:
        """
        Emit event.
        
        Args:
            event_name: Event name
            data: Event data
            
        Example:
            ```python
            await app.emit("user:created", {"id": 1, "name": "John"})
            ```
        """
        await self.event_bus.emit(event_name, data)
    
    # HTTP Methods
    
    def get(
        self,
        path: str,
        condition: Optional[Callable[[Any], bool]] = None,
        name: Optional[str] = None,
    ):
        """Register GET route."""
        return self.route(path, methods=["GET"], condition=condition, name=name)
    
    def post(
        self,
        path: str,
        condition: Optional[Callable[[Any], bool]] = None,
        name: Optional[str] = None,
    ):
        """Register POST route."""
        return self.route(path, methods=["POST"], condition=condition, name=name)
    
    def put(
        self,
        path: str,
        condition: Optional[Callable[[Any], bool]] = None,
        name: Optional[str] = None,
    ):
        """Register PUT route."""
        return self.route(path, methods=["PUT"], condition=condition, name=name)
    
    def delete(
        self,
        path: str,
        condition: Optional[Callable[[Any], bool]] = None,
        name: Optional[str] = None,
    ):
        """Register DELETE route."""
        return self.route(path, methods=["DELETE"], condition=condition, name=name)
    
    def patch(
        self,
        path: str,
        condition: Optional[Callable[[Any], bool]] = None,
        name: Optional[str] = None,
    ):
        """Register PATCH route."""
        return self.route(path, methods=["PATCH"], condition=condition, name=name)
    
    def route(
        self,
        path: str,
        methods: List[str] = None,
        condition: Optional[Callable[[Any], bool]] = None,
        name: Optional[str] = None,
    ):
        """
        Route decorator.
        
        Args:
            path: Route path pattern
            methods: HTTP methods
            condition: Optional condition function
            name: Optional route name
        """
        if methods is None:
            methods = ["GET"]
        
        def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
            # Apply hybrid executor to handler
            hybrid_handler = hybrid_executor(handler)
            
            # Preserve rate_limit attribute if present
            if hasattr(handler, '_rate_limit'):
                hybrid_handler._rate_limit = handler._rate_limit
            
            # Preserve cache_config attribute if present
            if hasattr(handler, '_cache_config'):
                hybrid_handler._cache_config = handler._cache_config
            
            # Register route
            self.router.add_route(path, hybrid_handler, methods, condition, name)
            
            # Add to OpenAPI generator (use original handler for signature extraction)
            for method in methods:
                self.openapi_generator.add_route(
                    path,
                    method,
                    handler,  # Use original handler, not hybrid_handler
                    summary=getattr(handler, "__name__", None),
                    description=handler.__doc__ or None,
                )
            
            return hybrid_handler
        
        return decorator
    
    def when(self, condition: Callable[[Any], bool]):
        """
        Conditional route decorator.
        
        Args:
            condition: Condition function that takes request and returns bool
        """
        def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
            # Apply hybrid executor
            hybrid_handler = hybrid_executor(handler)
            
            # Add to router with condition
            # Note: path will be determined by actual request
            hybrid_handler._route_condition = condition
            hybrid_handler._route_handler = hybrid_handler
            
            # Store conditional handler
            if not hasattr(self, "_conditional_handlers"):
                self._conditional_handlers = []
            self._conditional_handlers.append((condition, hybrid_handler))
            
            return hybrid_handler
        
        return decorator
    
    # Lifecycle Events
    
    def on_startup(self, handler: Callable[..., Any]) -> Callable[..., Any]:
        """Register startup handler."""
        self._startup_handlers.append(handler)
        return handler
    
    def on_shutdown(self, handler: Callable[..., Any]) -> Callable[..., Any]:
        """Register shutdown handler."""
        self._shutdown_handlers.append(handler)
        return handler
    
    # ASGI Interface
    
    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        """
        ASGI application interface.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Handle lifespan events (startup/shutdown)
        if scope["type"] == "lifespan":
            await self._handle_lifespan(scope, receive, send)
            return
        
        # Handle WebSocket connections
        if scope["type"] == "websocket":
            await self._handle_websocket(scope, receive, send)
            return
        
        # Handle OpenAPI documentation endpoints
        if scope["type"] == "http":
            path = scope.get("path", "/")
            
            # Handle OPTIONS (preflight) requests - must go through middleware for CORS
            if scope.get("method") == "OPTIONS":
                # Create request to process through middleware
                request = Request(scope, receive)
                
                # Create temporary handler for OPTIONS
                async def options_handler(req: Request) -> Response:
                    # For OPTIONS, just return empty response
                    return Response(status_code=204)
                
                # Create temporary middleware stack for OPTIONS
                options_middleware_stack = MiddlewareStack(options_handler)
                for middleware in self._middleware:
                    options_middleware_stack.add(middleware)
                
                # Process OPTIONS through middleware for CORS headers
                response = await options_middleware_stack(request)
                await response(send)
                return
            
            # Swagger UI
            if path == self.docs_url:
                html = SWAGGER_UI_HTML.format(title=self.title)
                response = HTMLResponse(html)
                # Add CORS headers for Swagger UI
                self._add_cors_headers(response, scope)
                await response(send)
                return
            
            # OpenAPI JSON (cached)
            elif path == self.openapi_url:
                cache_instance = get_cache()
                cache_key = f"openapi:{self.version}"
                
                # Try to get from cache
                cached_spec = cache_instance.get(cache_key)
                if cached_spec is not None:
                    response = JSONResponse(cached_spec)
                    response.headers["X-Cache"] = "HIT"
                else:
                    spec = self.openapi_generator.generate_spec()
                    # Cache for 1 hour
                    cache_instance.set(cache_key, spec, ttl=3600)
                    response = JSONResponse(spec)
                    response.headers["X-Cache"] = "MISS"
                
                # Add CORS headers for OpenAPI JSON
                self._add_cors_headers(response, scope)
                await response(send)
                return
        
        # Handle startup
        if not self._started:
            await self._run_startup_handlers()
            self._started = True
        
        # Create request
        request = Request(scope, receive)
        
        # Initialize middleware stack if needed
        if self.middleware_stack is None:
            # Create handler function
            async def handler(req: Request) -> Response:
                return await self._handle_request(req)
            
            self.middleware_stack = MiddlewareStack(handler)
            for middleware in self._middleware:
                self.middleware_stack.add(middleware)
        
        # Process through middleware
        response = await self.middleware_stack(request)
        
        # CORS headers should already be added by middleware, but ensure they are there
        if hasattr(response, 'headers') and 'Access-Control-Allow-Origin' not in response.headers:
            self._add_cors_headers(response, scope)
        
        await response(send)
    
    async def _handle_request(self, request: Request) -> Response:
        """Handle HTTP request (used by middleware stack)."""
        # Find route
        route_match = self.router.find_route(request.path, request.method, request)
        
        if route_match is None:
            # No route found - try conditional handlers
            if hasattr(self, "_conditional_handlers"):
                for condition, handler in self._conditional_handlers:
                    if condition(request):
                        result = await run_hybrid(handler, request)
                        # Convert result to Response if needed
                        # Handle tuple responses (data, status_code)
                        if isinstance(result, tuple) and len(result) == 2:
                            data, status_code = result
                            if isinstance(data, Response):
                                data.status_code = status_code
                                return data
                            elif isinstance(data, dict):
                                return JSONResponse(data, status_code=status_code)
                            else:
                                return JSONResponse({"result": data}, status_code=status_code)
                        elif isinstance(result, Response):
                            return result
                        elif isinstance(result, dict):
                            return JSONResponse(result)
                        elif isinstance(result, (str, int, float, bool, list)):
                            return JSONResponse({"result": result})
                        else:
                            return JSONResponse({"result": str(result)})
            
            # 404 Not Found
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        
        route, path_params = route_match
        
        handler = route.handler
        cache_instance = get_cache()
        
        # Check cache if configured (only for GET requests)
        cache_key = None
        if request.method == "GET" and hasattr(handler, '_cache_config'):
            cache_config = handler._cache_config
            
            # Generate cache key
            if cache_config.get('key_func'):
                cache_key = cache_config['key_func'](request)
            else:
                cache_key = generate_cache_key(
                    path=request.path,
                    method=request.method,
                    query_params=dict(request.query_params),
                    headers=request.headers,
                    include_headers=cache_config.get('include_headers', False),
                )
                # Add route identifier to avoid collisions
                cache_key = f"route:{cache_key}"
            
            # Try to get from cache
            cached_response = cache_instance.get(cache_key)
            if cached_response is not None:
                self.logger.debug(
                    f"Cache HIT for {request.path}",
                    path=request.path,
                    method=request.method,
                    extra={"event": "cache_hit"}
                )
                # Return cached response
                response = JSONResponse(cached_response)
                response.headers["X-Cache"] = "HIT"
                response.headers["X-Cache-Key"] = cache_key
                return response
        
        # Check rate limiting if configured
        if hasattr(handler, '_rate_limit'):
            rate_limit_config = handler._rate_limit
            rate_limiter = get_rate_limiter()
            
            # Generate rate limit key
            if rate_limit_config.get('key_func'):
                route_key = rate_limit_config['key_func'](request)
            else:
                route_key = f"{request.method}:{request.path}"
            
            # Get client IP
            client_ip = "unknown"
            if hasattr(request, "client") and request.client:
                if isinstance(request.client, tuple):
                    client_ip = request.client[0]
                else:
                    client_ip = str(request.client)
            
            # Check rate limit
            is_allowed, rate_info = rate_limiter.check_rate_limit(
                route_key=route_key,
                client_ip=client_ip if rate_limit_config.get('per_ip', True) else "global",
                requests_per_minute=rate_limit_config['requests_per_minute'],
                window_seconds=rate_limit_config.get('window_seconds', 60),
            )
            
            if not is_allowed:
                # Rate limit exceeded
                self.logger.warning(
                    f"Rate limit exceeded for {route_key} from {client_ip}",
                    route_key=route_key,
                    client_ip=client_ip,
                    limit=rate_info['limit'],
                    extra={"event": "rate_limit_exceeded"}
                )
                
                error_response = JSONResponse(
                    {
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {rate_info['limit']} requests per {rate_limit_config.get('window_seconds', 60)} seconds",
                        "limit": rate_info['limit'],
                        "retry_after": rate_info['retry_after'],
                    },
                    status_code=429,
                )
                
                # Add rate limit headers
                error_response.headers["X-RateLimit-Limit"] = str(rate_info['limit'])
                error_response.headers["X-RateLimit-Remaining"] = "0"
                error_response.headers["X-RateLimit-Reset"] = str(int(rate_info['reset_at']))
                error_response.headers["Retry-After"] = str(rate_info['retry_after'])
                
                return error_response
            
            # Add rate limit headers to successful response
            # (will be added later after response is created)
        
        try:
            # Prepare handler arguments (with automatic body extraction)
            handler_kwargs = await self._prepare_handler_args(
                route.handler, request, path_params
            )
            
            # Execute handler (hybrid - works with sync and async)
            result = await run_hybrid(route.handler, **handler_kwargs)
            
            # Convert result to Response if needed
            # Handle tuple responses (data, status_code)
            if isinstance(result, tuple) and len(result) == 2:
                data, status_code = result
                if isinstance(data, Response):
                    data.status_code = status_code
                    return data
                elif isinstance(data, dict):
                    return JSONResponse(data, status_code=status_code)
                else:
                    return JSONResponse({"result": data}, status_code=status_code)
            elif isinstance(result, Response):
                response = result
            elif isinstance(result, dict):
                response = JSONResponse(result)
            elif isinstance(result, (str, int, float, bool, list)):
                response = JSONResponse({"result": result})
            else:
                # Try to convert to JSON
                response = JSONResponse({"result": str(result)})
            
            # Add rate limit headers if rate limiting is configured
            if hasattr(handler, '_rate_limit'):
                rate_limit_config = handler._rate_limit
                rate_limiter = get_rate_limiter()
                
                # Generate rate limit key
                if rate_limit_config.get('key_func'):
                    route_key = rate_limit_config['key_func'](request)
                else:
                    route_key = f"{request.method}:{request.path}"
                
                # Get client IP
                client_ip = "unknown"
                if hasattr(request, "client") and request.client:
                    if isinstance(request.client, tuple):
                        client_ip = request.client[0]
                    else:
                        client_ip = str(request.client)
                
                # Get current rate limit info
                rate_info = rate_limiter.get_rate_limit_info(
                    route_key=route_key,
                    client_ip=client_ip if rate_limit_config.get('per_ip', True) else "global",
                    requests_per_minute=rate_limit_config['requests_per_minute'],
                    window_seconds=rate_limit_config.get('window_seconds', 60),
                )
                
                # Add rate limit headers
                response.headers["X-RateLimit-Limit"] = str(rate_info['limit'])
                response.headers["X-RateLimit-Remaining"] = str(rate_info['remaining'])
                response.headers["X-RateLimit-Reset"] = str(int(rate_info['reset_at']))
            
            # Cache response if configured (only for GET requests)
            if (
                cache_key is not None
                and request.method == "GET"
                and hasattr(handler, '_cache_config')
                and isinstance(response, JSONResponse)
            ):
                cache_config = handler._cache_config
                
                # Extract response data
                try:
                    import json as json_module
                    response_body = response.content
                    if isinstance(response_body, bytes):
                        response_data = json_module.loads(response_body.decode())
                    else:
                        response_data = response_body
                    
                    # Only cache successful responses
                    if response.status_code == 200:
                        cache_instance.set(
                            cache_key,
                            response_data,
                            ttl=cache_config['ttl']
                        )
                        
                        self.logger.debug(
                            f"Cache SET for {request.path} (TTL: {cache_config['ttl']}s)",
                            path=request.path,
                            method=request.method,
                            ttl=cache_config['ttl'],
                            extra={"event": "cache_set"}
                        )
                        response.headers["X-Cache"] = "MISS"
                        response.headers["X-Cache-Key"] = cache_key
                        response.headers["X-Cache-TTL"] = str(cache_config['ttl'])
                except Exception as e:
                    # If caching fails, log but don't fail the request
                    self.logger.warning(
                        f"Failed to cache response: {str(e)}",
                        path=request.path,
                        extra={"event": "cache_error"}
                    )
            
            return response
        
        except HTTPException as exc:
            # HTTP exceptions (ValidationError, NotFoundError, etc.)
            if isinstance(exc, HTTPValidationError) and hasattr(exc, 'to_dict'):
                error_data = exc.to_dict()
            else:
                error_data = {"error": exc.detail}
            
            error_response = JSONResponse(error_data, status_code=exc.status_code)
            # Add custom headers if any
            if exc.headers:
                error_response.headers.update(exc.headers)
            return error_response
        
        except Exception as exc:
            # Other exceptions
            # Log the error
            self.logger.error(
                f"Unhandled exception in handler: {str(exc)}",
                exc_info=True,
                path=request.path,
                method=request.method,
                extra={"event": "unhandled_exception"}
            )
            
            if self.debug:
                import traceback
                error_response = JSONResponse({
                    "error": str(exc),
                    "traceback": traceback.format_exc()
                }, status_code=500)
            else:
                error_response = JSONResponse({
                    "error": "Internal Server Error"
                }, status_code=500)
            return error_response
    
    async def _prepare_handler_args(
        self,
        handler: Callable[..., Any],
        request: Request,
        path_params: Dict[str, str],
    ) -> Dict[str, Any]:
        """Prepare arguments for handler function with automatic body extraction."""
        sig = inspect.signature(handler)
        kwargs: Dict[str, Any] = {}
        
        for param_name, param in sig.parameters.items():
            # Dependency Injection - check if parameter has Depends() as default
            if isinstance(param.default, Dependency):
                # Will be resolved later
                kwargs[param_name] = param.default
                continue
            
            param_type = param.annotation
            
            # Path parameters
            if param_name in path_params:
                value = path_params[param_name]
                # Validate and convert type
                if param.annotation != inspect.Parameter.empty:
                    try:
                        value = validate_path_param(value, param.annotation)
                    except ValidationError as e:
                        raise HTTPValidationError(
                            f"Invalid path parameter '{param_name}': {str(e)}",
                            errors={param_name: [str(e)]}
                        )
                kwargs[param_name] = value
            
            # Request object - check by annotation or by name
            elif (
                param_name == "request" or
                param.annotation == Request or
                (hasattr(param.annotation, "__name__") and param.annotation.__name__ == "Request")
            ):
                kwargs[param_name] = request
            
            # Query parameters
            elif param_name in request.query_params:
                values = request.query_params[param_name]
                value = values[0] if values else None
                
                # Validate query parameter type
                if param.annotation != inspect.Parameter.empty and value is not None:
                    try:
                        value = validate_query_param(value, param.annotation)
                    except ValidationError as e:
                        raise HTTPValidationError(
                            f"Invalid query parameter '{param_name}': {str(e)}",
                            errors={param_name: [str(e)]}
                        )
                
                kwargs[param_name] = value
            
            # File upload (FileUpload type)
            elif param_type != inspect.Parameter.empty and (
                param_type == FileUpload or
                (hasattr(param_type, "__name__") and param_type.__name__ == "FileUpload")
            ):
                # Check if request is multipart
                content_type = request.headers.get("content-type", "")
                if not content_type.startswith("multipart/form-data"):
                    if param.default == inspect.Parameter.empty:
                        raise HTTPValidationError(
                            f"File upload requires multipart/form-data, got {content_type}",
                            errors={param_name: ["Content-Type must be multipart/form-data"]}
                        )
                    else:
                        kwargs[param_name] = param.default
                else:
                    # Get files from multipart request
                    files = await request.files()
                    file = files.get(param_name)
                    
                    if file is None:
                        if param.default == inspect.Parameter.empty:
                            raise HTTPValidationError(
                                f"File '{param_name}' is required",
                                errors={param_name: ["File is required"]}
                            )
                        else:
                            kwargs[param_name] = param.default
                    else:
                        kwargs[param_name] = file
            
            # Request body (automatic extraction for POST, PUT, PATCH)
            elif request.method in ("POST", "PUT", "PATCH"):
                param_type = param.annotation
                
                # Check if it's a model class that needs validation
                if param_type != inspect.Parameter.empty and inspect.isclass(param_type):
                    # Check if it's a dataclass or has annotations (validation candidate)
                    from dataclasses import is_dataclass
                    needs_validation = (
                        is_dataclass(param_type) or 
                        hasattr(param_type, "__annotations__")
                    )
                    
                    if needs_validation:
                        # Extract and validate body
                        try:
                            body_data = await request.json(default=None)
                            
                            if body_data is None:
                                if param.default == inspect.Parameter.empty:
                                    raise HTTPValidationError(
                                        f"Request body is required for parameter '{param_name}'",
                                        errors={param_name: ["Request body is required"]}
                                    )
                                else:
                                    kwargs[param_name] = param.default
                            else:
                                # Validate using validation system
                                try:
                                    kwargs[param_name] = validate_request_body(body_data, param_type)
                                except ValidationError as e:
                                    raise HTTPValidationError(
                                        f"Validation failed for '{param_name}': {e.message}",
                                        errors=e.errors
                                    )
                        except ValueError as e:
                            # JSON parsing error
                            raise HTTPValidationError(
                                f"Invalid JSON in request body: {str(e)}",
                                errors={"body": [str(e)]}
                            )
                    else:
                        # Regular class, try to instantiate without validation
                        try:
                            body_data = await request.json(default=None)
                            if body_data is None:
                                if param.default == inspect.Parameter.empty:
                                    raise HTTPValidationError(
                                        f"Request body is required for parameter '{param_name}'"
                                    )
                                else:
                                    kwargs[param_name] = param.default
                            else:
                                try:
                                    kwargs[param_name] = param_type(**body_data)
                                except Exception as e:
                                    raise HTTPValidationError(
                                        f"Failed to create {param_type.__name__}: {str(e)}"
                                    )
                        except ValueError as e:
                            raise HTTPValidationError(f"Invalid JSON: {str(e)}")
            
            # Default value
            elif param.default != inspect.Parameter.empty:
                kwargs[param_name] = param.default
        
        # Resolve dependencies asynchronously
        dependencies_to_resolve = {
            name: value for name, value in kwargs.items()
            if isinstance(value, Dependency)
        }
        
        if dependencies_to_resolve:
            resolved = await resolve_dependency_values(
                dependencies_to_resolve,
                request=request,
                **path_params
            )
            kwargs.update(resolved)
        
        return kwargs
    
    async def _send_response(self, response: Any, send: Any) -> None:
        """Send response via ASGI send."""
        if not isinstance(response, Response):
            # Convert to JSONResponse if dict or other
            if isinstance(response, dict):
                response = JSONResponse(response)
            elif isinstance(response, str):
                response = JSONResponse({"message": response})
            else:
                response = JSONResponse({"data": str(response)})
        
        # Send via ASGI
        headers = response._prepare_headers()
        
        await send({
            "type": "http.response.start",
            "status": response.status_code,
            "headers": headers,
        })
        
        body = response._get_body()
        await send({
            "type": "http.response.body",
            "body": body,
        })
    
    async def _handle_lifespan(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """Handle ASGI lifespan events (startup/shutdown)."""
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await self._run_startup_handlers()
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await self._run_shutdown_handlers()
                await send({"type": "lifespan.shutdown.complete"})
                break
    
    async def _run_startup_handlers(self) -> None:
        """Run startup handlers."""
        for handler in self._startup_handlers:
            await run_hybrid(handler)
    
    async def _run_shutdown_handlers(self) -> None:
        """Run shutdown handlers."""
        for handler in self._shutdown_handlers:
            await run_hybrid(handler)
    
    async def _handle_websocket(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """Handle WebSocket connection."""
        path = scope.get("path", "/")
        
        # Find WebSocket route
        for route in self._websocket_routes:
            path_params = route.match(path)
            if path_params is not None:
                # Create WebSocket instance
                websocket = WebSocket(scope, receive, send)
                
                # Prepare handler arguments
                sig = inspect.signature(route.handler)
                kwargs: Dict[str, Any] = {}
                
                for param_name, param in sig.parameters.items():
                    # WebSocket object
                    if param.annotation == WebSocket or (
                        hasattr(param.annotation, "__name__")
                        and param.annotation.__name__ == "WebSocket"
                    ):
                        kwargs[param_name] = websocket
                    # Path parameters
                    elif param_name in path_params:
                        value = path_params[param_name]
                        # Try to convert type
                        if param.annotation != inspect.Parameter.empty:
                            try:
                                if param.annotation == int:
                                    value = int(value)
                                elif param.annotation == float:
                                    value = float(value)
                                elif param.annotation == bool:
                                    value = value.lower() in ("true", "1", "yes", "on")
                            except (ValueError, TypeError):
                                pass
                        kwargs[param_name] = value
                    # Default value
                    elif param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                
                # Execute handler
                try:
                    await run_hybrid(route.handler, **kwargs)
                except Exception as exc:
                    if self.debug:
                        raise
                    # Close WebSocket on error
                    try:
                        await websocket.close(code=1011)  # Internal error
                    except Exception:
                        pass
                return
        
        # No route found - reject connection
        await send({"type": "websocket.close", "code": 1003})  # Unsupported
    
    def _add_cors_headers(self, response: Response, scope: Dict[str, Any]) -> None:
        """Add CORS headers to response."""
        # Check if CORS middleware is enabled
        cors_middleware = None
        for middleware in self._middleware:
            if middleware.__class__.__name__ == "CORSMiddleware":
                cors_middleware = middleware
                break
        
        if not cors_middleware:
            return
        
        # Extract origin from headers
        origin = None
        try:
            headers_list = scope.get("headers", [])
            if isinstance(headers_list, list):
                for item in headers_list:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        key, value = item[0], item[1]
                        if isinstance(key, bytes) and key.lower() == b"origin":
                            if isinstance(value, bytes):
                                origin = value.decode("utf-8")
                            else:
                                origin = str(value)
                            break
        except Exception:
            pass
        
        # Add CORS headers
        if "*" in cors_middleware.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
        elif origin and origin in cors_middleware.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        # Add other CORS headers
        if "*" in cors_middleware.allow_methods:
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD"
        else:
            response.headers["Access-Control-Allow-Methods"] = ", ".join(cors_middleware.allow_methods)
        
        if "*" in cors_middleware.allow_headers:
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, X-Requested-With, Origin"
        else:
            response.headers["Access-Control-Allow-Headers"] = ", ".join(cors_middleware.allow_headers)
        
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "Content-Type, Content-Length, Authorization"
        response.headers["Access-Control-Max-Age"] = "3600"
