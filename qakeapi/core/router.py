"""
Routing system for QakeAPI
"""

import re
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union
from enum import Enum
import inspect

from .request import Request
from .response import Response, JSONResponse
from .websocket import WebSocket
from .exceptions import HTTPException, MethodNotAllowedException, NotFoundException
from .dependencies import DependencyResolver
from ..utils.status import status


class RouteType(Enum):
    """Route types"""

    HTTP = "http"
    WEBSOCKET = "websocket"


class Route:
    """Route class"""

    def __init__(
        self,
        path: str,
        handler: Callable[..., Any],
        methods: List[str],
        route_type: RouteType = RouteType.HTTP,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        self.path = path
        self.handler = handler
        self.methods = [method.upper() for method in methods]
        self.route_type = route_type
        self.name = name or handler.__name__
        self.include_in_schema = include_in_schema

        # Compile regular expression for path
        self.path_regex, self.path_params = self._compile_path(path)

    def _compile_path(self, path: str) -> Tuple[Pattern[str], List[str]]:
        """
        Compile path to regular expression

        Supported formats:
        - /users/{user_id} - path parameter
        - /users/{user_id:int} - typed parameter
        - /files/{path:path} - path parameter (can contain slashes)
        """
        param_names = []
        regex_parts = []

        # Split path into parts
        parts = path.split("/")

        for part in parts:
            if not part:
                continue

            if part.startswith("{") and part.endswith("}"):
                # This is a path parameter
                param_spec = part[1:-1]  # Remove { and }

                if ":" in param_spec:
                    param_name, param_type = param_spec.split(":", 1)
                else:
                    param_name = param_spec
                    param_type = "str"

                param_names.append(param_name)

                # Define regular expression for type
                if param_type == "int":
                    regex_parts.append(r"([0-9]+)")
                elif param_type == "float":
                    regex_parts.append(r"([0-9]*\.?[0-9]+)")
                elif param_type == "uuid":
                    regex_parts.append(
                        r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
                    )
                elif param_type == "path":
                    regex_parts.append(r"(.+)")
                else:  # str
                    regex_parts.append(r"([^/]+)")
            else:
                # Regular part of path
                regex_parts.append(re.escape(part))

        # Assemble full regular expression
        if regex_parts:
            pattern = "^/" + "/".join(regex_parts)
            # If path ends with /, make slash optional
            if path.endswith("/") and path != "/":
                pattern += "/?$"
            else:
                pattern += "$"
        else:
            pattern = "^/$"

        return re.compile(pattern), param_names

    def matches(self, path: str, method: str) -> Optional[Dict[str, str]]:
        """
        Check if route matches path and method

        Returns:
            Dictionary with path parameters or None if not matching
        """
        if self.route_type == RouteType.HTTP and method not in self.methods:
            return None

        match = self.path_regex.match(path)
        if not match:
            return None

        # Extract path parameters
        path_params = {}
        for i, param_name in enumerate(self.path_params):
            path_params[param_name] = match.group(i + 1)

        return path_params


class APIRouter:
    """Class for grouping routes"""

    def __init__(
        self,
        prefix: str = "",
        tags: Optional[List[str]] = None,
        dependencies: Optional[List[Any]] = None,
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
    ) -> None:
        self.prefix = prefix.rstrip("/")
        self.tags = tags or []
        self.dependencies = dependencies or []
        self.responses = responses or {}
        self.routes: List[Route] = []
        self.dependency_resolver = DependencyResolver()

    def add_route(
        self,
        path: str,
        handler: Callable[..., Any],
        methods: List[str],
        route_type: RouteType = RouteType.HTTP,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        """Add route"""
        full_path = self.prefix + path
        route = Route(
            path=full_path,
            handler=handler,
            methods=methods,
            route_type=route_type,
            name=name,
            include_in_schema=include_in_schema,
        )
        self.routes.append(route)

    def get(
        self,
        path: str,
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for GET requests"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_route(
                path=path,
                handler=func,
                methods=["GET"],
                name=name,
                include_in_schema=include_in_schema,
            )
            return func

        return decorator

    def post(
        self,
        path: str,
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for POST requests"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_route(
                path=path,
                handler=func,
                methods=["POST"],
                name=name,
                include_in_schema=include_in_schema,
            )
            return func

        return decorator

    def put(
        self,
        path: str,
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for PUT requests"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_route(
                path=path,
                handler=func,
                methods=["PUT"],
                name=name,
                include_in_schema=include_in_schema,
            )
            return func

        return decorator

    def delete(
        self,
        path: str,
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for DELETE requests"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_route(
                path=path,
                handler=func,
                methods=["DELETE"],
                name=name,
                include_in_schema=include_in_schema,
            )
            return func

        return decorator

    def patch(
        self,
        path: str,
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for PATCH requests"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_route(
                path=path,
                handler=func,
                methods=["PATCH"],
                name=name,
                include_in_schema=include_in_schema,
            )
            return func

        return decorator

    def options(
        self,
        path: str,
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for OPTIONS requests"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_route(
                path=path,
                handler=func,
                methods=["OPTIONS"],
                name=name,
                include_in_schema=include_in_schema,
            )
            return func

        return decorator

    def head(
        self,
        path: str,
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for HEAD requests"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_route(
                path=path,
                handler=func,
                methods=["HEAD"],
                name=name,
                include_in_schema=include_in_schema,
            )
            return func

        return decorator

    def websocket(
        self,
        path: str,
        *,
        name: Optional[str] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for WebSocket connections"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_route(
                path=path,
                handler=func,
                methods=["GET"],  # WebSocket uses GET for handshake
                route_type=RouteType.WEBSOCKET,
                name=name,
                include_in_schema=False,
            )
            return func

        return decorator

    def route(
        self,
        path: str,
        methods: List[str],
        *,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for arbitrary HTTP methods"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_route(
                path=path,
                handler=func,
                methods=methods,
                name=name,
                include_in_schema=include_in_schema,
            )
            return func

        return decorator

    def include_router(
        self,
        router: "APIRouter",
        *,
        prefix: str = "",
        tags: Optional[List[str]] = None,
    ) -> None:
        """Include another router"""
        # If router has its own prefix, use it
        # Otherwise use passed prefix
        if router.prefix:
            # Router already has prefix, just add its routes
            full_prefix = self.prefix + router.prefix
        else:
            # Router without prefix, apply passed prefix
            full_prefix = self.prefix + prefix

        for route in router.routes:
            # Create new route with correct prefix
            if router.prefix and route.path.startswith(router.prefix):
                # Route already contains router prefix
                new_path = self.prefix + route.path
            else:
                # Route without router prefix, add full prefix
                new_path = full_prefix + route.path
            new_route = Route(
                path=new_path,
                handler=route.handler,
                methods=route.methods,
                route_type=route.route_type,
                name=route.name,
                include_in_schema=route.include_in_schema,
            )
            self.routes.append(new_route)

    async def handle_request(self, request: Request) -> Response:
        """Handle HTTP request"""
        path = request.path
        method = request.method

        # Find matching route
        matched_route = None
        path_params = None
        allowed_methods = set()

        for route in self.routes:
            if route.route_type != RouteType.HTTP:
                continue

            params = route.matches(path, method)
            if params is not None:
                matched_route = route
                path_params = params
                break

            # Check if path matches for other methods
            if route.path_regex.match(path):
                allowed_methods.update(route.methods)

        if matched_route is None:
            if allowed_methods:
                # Path found, but method not allowed
                raise MethodNotAllowedException(
                    f"Method {method} not allowed",
                    headers={"Allow": ", ".join(sorted(allowed_methods))},
                )
            else:
                # Path not found
                raise NotFoundException(f"Path {path} not found")

        # Set path parameters in request
        if path_params:
            request.set_path_params(path_params)

        # Resolve dependencies
        dependencies = await self.dependency_resolver.resolve_dependencies(
            matched_route.handler, request, path_params
        )

        # Call handler
        try:
            if inspect.iscoroutinefunction(matched_route.handler):
                result = await matched_route.handler(**dependencies)
            else:
                result = matched_route.handler(**dependencies)

            # Convert result to Response
            if isinstance(result, Response):
                return result
            elif isinstance(result, dict):
                return JSONResponse(result)
            elif isinstance(result, (list, tuple)):
                return JSONResponse(result)
            elif isinstance(result, str):
                return Response(result, media_type="text/plain")
            elif result is None:
                return Response(status_code=status.NO_CONTENT)
            else:
                return JSONResponse(result)
        except Exception as exc:
            # Re-raise exception to be handled by application's exception handler
            raise exc
        finally:
            # Clear dependency cache after request processing
            self.dependency_resolver.clear_cache()

    async def handle_websocket(self, websocket: WebSocket) -> None:
        """Handle WebSocket connection"""
        path = websocket.path

        # Find matching WebSocket route
        matched_route = None
        path_params = None

        for route in self.routes:
            if route.route_type != RouteType.WEBSOCKET:
                continue

            params = route.matches(path, "GET")
            if params is not None:
                matched_route = route
                path_params = params
                break

        if matched_route is None:
            await websocket.close(code=1000, reason="Route not found")
            return

        # Create fake request object for dependency resolution
        fake_request = Request(websocket._scope, websocket._receive)
        if path_params:
            fake_request.set_path_params(path_params)

        # Resolve dependencies
        dependencies = await self.dependency_resolver.resolve_dependencies(
            matched_route.handler, fake_request, path_params
        )

        # Add WebSocket to dependencies
        dependencies["websocket"] = websocket

        # Call handler
        try:
            if inspect.iscoroutinefunction(matched_route.handler):
                await matched_route.handler(**dependencies)
            else:
                matched_route.handler(**dependencies)
        finally:
            # Clear dependency cache
            self.dependency_resolver.clear_cache()
