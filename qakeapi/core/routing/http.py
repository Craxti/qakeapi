"""HTTP routing implementation."""
import re
import logging
import asyncio
from typing import Any, Callable, Dict, List, Optional, Pattern, Union

from ..requests import Request
from ..responses import Response
from .base import BaseRoute, BaseRouter, RouteMatch

logger = logging.getLogger(__name__)

class HTTPRoute(BaseRoute):
    """HTTP route implementation."""
    
    def __init__(self, 
                 path: str, 
                 handler: Callable, 
                 methods: List[str], 
                 name: Optional[str] = None):
        super().__init__(path, handler, name)
        self.methods = [m.upper() for m in methods]
        logger.debug(f"Created HTTP route: {path} {methods}")
    
    def _compile_pattern(self, path: str) -> Pattern:
        """Compile path pattern to regex."""
        pattern = re.sub(r"{([^:}]+)(?::([^}]+))?}", r"(?P<\1>[^/]+)", path)
        return re.compile(f"^{pattern}$")
    
    def match(self, path: str) -> Optional[Dict[str, str]]:
        """Check if path matches route pattern."""
        match = self.pattern.match(path)
        if match:
            logger.debug(f"Route {self.path} matches {path}")
            return match.groupdict()
        logger.debug(f"Route {self.path} does not match {path}")
        return None

class HTTPRouter(BaseRouter):
    """HTTP router implementation."""
    def __init__(self):
        super().__init__()
        # path -> method -> HTTPRoute
        self._routes_dict: Dict[str, Dict[str, HTTPRoute]] = {}

    @property
    def routes(self) -> List[HTTPRoute]:
        """Get routes as list for compatibility with tests."""
        return self._routes

    def add_route(self, 
                 path: str, 
                 handler: Callable, 
                 methods: List[str] = None, 
                 name: Optional[str] = None) -> None:
        """Add HTTP route."""
        if methods is None:
            methods = ["GET"]
        if path not in self._routes_dict:
            self._routes_dict[path] = {}
        
        # Check if route already exists and update it
        existing_route = None
        for route in self._routes:
            if route.path == path:
                existing_route = route
                break
        
        if existing_route:
            # Update existing route
            existing_route.handler = handler
            existing_route.name = name
            for method in methods:
                self._routes_dict[path][method.upper()] = existing_route
        else:
            # Create new route
            for method in methods:
                route = HTTPRoute(path, handler, [method.upper()], name)
                self._routes_dict[path][method.upper()] = route
                self._routes.append(route)
        
        logger.debug(f"Added HTTP route: {path} {methods}")

    def route(self, path: str, methods: List[str] = None, name: Optional[str] = None):
        """Route decorator."""
        def decorator(handler: Callable) -> Callable:
            self.add_route(path, handler, methods, name)
            return handler
        return decorator

    async def handle_request(self, request: Request) -> Response:
        """Handle HTTP request."""
        try:
            logger.debug(f"Handling request: {request.method} {request.path}")
            path = request.path
            method = request.method.upper()
            for route_path, method_map in self._routes_dict.items():
                # Используем любой route для match (pattern одинаковый для всех методов)
                route = next(iter(method_map.values()))
                params = route.match(path)
                if params is not None:
                    if method in method_map:
                        logger.debug(f"Found matching route: {route_path} with method: {method}")
                        # Add path parameters to request
                        request.path_params.update(params)
                        # Apply middleware chain
                        handler = method_map[method].handler
                        for middleware in reversed(self._middleware):
                            if asyncio.iscoroutinefunction(middleware):
                                prev_handler = handler
                                async def wrapped_handler(req, prev_handler=prev_handler):
                                    return await middleware(req, prev_handler)
                                handler = wrapped_handler
                            else:
                                handler = middleware(handler)
                        # Handle request
                        logger.debug(f"Calling handler for {route_path} [{method}]")
                        response = await handler(request)
                        if not isinstance(response, Response):
                            response = Response.json(response)
                        return response
                    else:
                        logger.debug(f"Method {method} not allowed for {route_path}. Allowed: {list(method_map.keys())}")
                        return Response.json({"detail": "Method not allowed"}, status_code=405)
            logger.debug(f"No route found for {request.path}")
            return Response.json({"detail": "Not found"}, status_code=404)
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}", exc_info=True)
            return Response.json({"detail": "Internal server error"}, status_code=500) 