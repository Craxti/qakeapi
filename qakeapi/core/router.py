"""
Router class for route registration and matching.

This module provides the Router and APIRouter classes for managing
HTTP routes and WebSocket routes.
"""

import re
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import defaultdict


class Route:
    """Represents a single route with its handler and metadata."""

    def __init__(
        self,
        path: str,
        handler: Callable,
        methods: List[str],
        name: Optional[str] = None,
    ):
        """
        Initialize route.

        Args:
            path: Route path pattern
            handler: Route handler function
            methods: List of HTTP methods
            name: Optional route name
        """
        self.path = path
        self.handler = handler
        self.methods = [m.upper() for m in methods]
        self.name = name
        self.pattern, self.param_names = self._compile_pattern(path)

    def _compile_pattern(self, path: str) -> Tuple[re.Pattern, List[str]]:
        """
        Compile path pattern to regex and extract parameter names.

        Args:
            path: Route path pattern (e.g., "/users/{user_id}")

        Returns:
            Tuple of (compiled regex pattern, list of parameter names)
        """
        # Find all {param} patterns
        param_pattern = r"\{([^}]+)\}"
        param_names = re.findall(param_pattern, path)

        # Build regex pattern
        # Escape the path but keep {} unescaped
        pattern_parts = []
        last_end = 0

        for match in re.finditer(param_pattern, path):
            # Add escaped text before the parameter
            before = path[last_end : match.start()]
            pattern_parts.append(re.escape(before))
            # Add parameter as named group
            param_name = match.group(1)
            pattern_parts.append(f"(?P<{param_name}>[^/]+)")
            last_end = match.end()

        # Add remaining text
        if last_end < len(path):
            pattern_parts.append(re.escape(path[last_end:]))

        # Compile regex
        pattern_str = "".join(pattern_parts)
        regex = re.compile(f"^{pattern_str}$")

        return regex, param_names

    def match(self, path: str) -> Optional[Dict[str, str]]:
        """
        Match path against route pattern.

        Args:
            path: Request path

        Returns:
            Dictionary of path parameters if match, None otherwise
        """
        match = self.pattern.match(path)
        if match:
            return match.groupdict()
        return None


class Router:
    """
    Base router class for managing routes.

    Handles route registration, matching, and parameter extraction.
    """

    def __init__(self):
        """Initialize router."""
        self.routes: List[Route] = []
        self.route_map: Dict[str, Dict[str, Route]] = defaultdict(dict)

    def add_route(
        self,
        path: str,
        handler: Callable,
        methods: List[str],
        name: Optional[str] = None,
    ):
        """
        Add a route to the router.

        Args:
            path: Route path pattern
            handler: Route handler function
            methods: List of HTTP methods
            name: Optional route name
        """
        route = Route(path, handler, methods, name)
        self.routes.append(route)

        # Index by method for faster lookup
        for method in route.methods:
            self.route_map[method][path] = route

    def find_route(
        self, path: str, method: str
    ) -> Optional[Tuple[Route, Dict[str, str]]]:
        """
        Find matching route for path and method.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            Tuple of (Route, path_params) if found, None otherwise
        """
        method = method.upper()

        # First try exact match
        if method in self.route_map:
            for route_path, route in self.route_map[method].items():
                if route_path == path:
                    return route, {}

        # Then try pattern matching
        for route in self.routes:
            if method in route.methods:
                params = route.match(path)
                if params is not None:
                    return route, params

        return None

    def get(self, path: str, name: Optional[str] = None):
        """
        Decorator for GET routes.

        Args:
            path: Route path
            name: Optional route name

        Returns:
            Decorator function
        """

        def decorator(handler: Callable) -> Callable:
            self.add_route(path, handler, ["GET"], name)
            return handler

        return decorator

    def post(self, path: str, name: Optional[str] = None):
        """
        Decorator for POST routes.

        Args:
            path: Route path
            name: Optional route name

        Returns:
            Decorator function
        """

        def decorator(handler: Callable) -> Callable:
            self.add_route(path, handler, ["POST"], name)
            return handler

        return decorator

    def put(self, path: str, name: Optional[str] = None):
        """
        Decorator for PUT routes.

        Args:
            path: Route path
            name: Optional route name

        Returns:
            Decorator function
        """

        def decorator(handler: Callable) -> Callable:
            self.add_route(path, handler, ["PUT"], name)
            return handler

        return decorator

    def delete(self, path: str, name: Optional[str] = None):
        """
        Decorator for DELETE routes.

        Args:
            path: Route path
            name: Optional route name

        Returns:
            Decorator function
        """

        def decorator(handler: Callable) -> Callable:
            self.add_route(path, handler, ["DELETE"], name)
            return handler

        return decorator

    def patch(self, path: str, name: Optional[str] = None):
        """
        Decorator for PATCH routes.

        Args:
            path: Route path
            name: Optional route name

        Returns:
            Decorator function
        """

        def decorator(handler: Callable) -> Callable:
            self.add_route(path, handler, ["PATCH"], name)
            return handler

        return decorator


class APIRouter(Router):
    """
    API Router with additional features like prefixes and tags.

    Extends Router with support for route grouping and metadata.
    """

    def __init__(self, prefix: str = "", tags: Optional[List[str]] = None):
        """
        Initialize API router.

        Args:
            prefix: Route prefix (e.g., "/api/v1")
            tags: Optional tags for OpenAPI documentation
        """
        super().__init__()
        self.prefix = prefix.rstrip("/")
        self.tags = tags or []

    def add_route(
        self,
        path: str,
        handler: Callable,
        methods: List[str],
        name: Optional[str] = None,
    ):
        """
        Add route with prefix.

        Args:
            path: Route path (will be prefixed)
            handler: Route handler function
            methods: List of HTTP methods
            name: Optional route name
        """
        # Add prefix to path
        full_path = f"{self.prefix}{path}"
        super().add_route(full_path, handler, methods, name)

    def include_router(self, router: "APIRouter", prefix: str = ""):
        """
        Include another router's routes.

        Args:
            router: Router to include
            prefix: Additional prefix for included routes
        """
        for route in router.routes:
            # Adjust path with prefixes
            new_path = f"{prefix}{route.path}"
            self.add_route(new_path, route.handler, route.methods, route.name)
