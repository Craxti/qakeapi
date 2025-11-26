"""
Smart Router - Intelligent routing with conditional matching.

This module provides routing functionality with conditional matching,
allowing routes to be selected based on custom conditions.
"""

import re
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import defaultdict


class Route:
    """Represents a single route."""
    
    def __init__(
        self,
        path: str,
        handler: Callable[..., Any],
        methods: List[str],
        condition: Optional[Callable[[Any], bool]] = None,
        name: Optional[str] = None,
    ):
        """
        Initialize route.
        
        Args:
            path: Route path pattern (e.g., "/users/{id}")
            handler: Route handler function
            methods: HTTP methods (GET, POST, etc.)
            condition: Optional condition function for conditional routing
            name: Optional route name
        """
        self.path = path
        self.handler = handler
        self.methods = [m.upper() for m in methods]
        self.condition = condition
        self.name = name
        self.pattern, self.param_names = self._compile_pattern(path)
    
    def _compile_pattern(self, path: str) -> Tuple[re.Pattern, List[str]]:
        """Compile path pattern to regex."""
        param_pattern = r"\{([^}]+)\}"
        param_names = re.findall(param_pattern, path)
        
        # Build regex pattern
        pattern_parts = []
        last_end = 0
        
        for match in re.finditer(param_pattern, path):
            before = path[last_end : match.start()]
            pattern_parts.append(re.escape(before))
            pattern_parts.append(f"(?P<{match.group(1)}>[^/]+)")
            last_end = match.end()
        
        if last_end < len(path):
            pattern_parts.append(re.escape(path[last_end:]))
        
        pattern_str = "".join(pattern_parts)
        regex = re.compile(f"^{pattern_str}$")
        
        return regex, param_names
    
    def match(self, path: str, method: str, request: Any = None) -> Optional[Dict[str, str]]:
        """
        Match route against path and method.
        
        Args:
            path: Request path
            method: HTTP method
            request: Request object (for conditional routing)
            
        Returns:
            Dictionary of path parameters if match, None otherwise
        """
        # Check method
        if method.upper() not in self.methods:
            return None
        
        # Check path pattern
        match = self.pattern.match(path)
        if not match:
            return None
        
        # Check condition if present
        if self.condition is not None and request is not None:
            if not self.condition(request):
                return None
        
        return match.groupdict()


class RouteTrie:
    """
    Trie structure for fast route lookup.
    
    Optimizes route finding for static paths (without parameters).
    Routes with parameters are stored separately.
    """
    
    def __init__(self):
        """Initialize Trie."""
        self.root: Dict[str, Any] = {}
        self.routes: Dict[str, Route] = {}  # path -> Route mapping for static routes
    
    def add(self, path: str, route: Route) -> None:
        """
        Add route to Trie.
        
        Args:
            path: Route path
            route: Route object
        """
        # Check if path has parameters
        if "{" in path or "}" in path:
            # Route with parameters - store separately
            return
        
        # Static route - add to Trie
        self.routes[path] = route
        node = self.root
        parts = path.split("/")
        
        for part in parts:
            if not part:
                continue
            if part not in node:
                node[part] = {}
            node = node[part]
        
        node["__route__"] = route
    
    def find(self, path: str) -> Optional[Route]:
        """
        Find route in Trie.
        
        Args:
            path: Request path
            
        Returns:
            Route if found, None otherwise
        """
        # Fast lookup for static paths
        if path in self.routes:
            return self.routes[path]
        
        # Try Trie traversal
        node = self.root
        parts = path.split("/")
        
        for part in parts:
            if not part:
                continue
            if part not in node:
                return None
            node = node[part]
        
        return node.get("__route__")


class Router:
    """
    Smart router with conditional routing support and optimized lookup.
    
    Supports:
    - Path-based routing with parameters
    - Conditional routing based on request properties
    - Multiple HTTP methods per route
    - Optimized Trie-based lookup for static routes
    """
    
    def __init__(self):
        """Initialize router."""
        self.routes: List[Route] = []
        self.conditional_routes: List[Route] = []
        self.static_trie = RouteTrie()
        self._trie_built = False
    
    def add_route(
        self,
        path: str,
        handler: Callable[..., Any],
        methods: List[str] = None,
        condition: Optional[Callable[[Any], bool]] = None,
        name: Optional[str] = None,
    ) -> None:
        """
        Add route to router.
        
        Args:
            path: Route path pattern
            handler: Handler function
            methods: HTTP methods (default: ["GET"])
            condition: Optional condition function
            name: Optional route name
        """
        if methods is None:
            methods = ["GET"]
        
        route = Route(path, handler, methods, condition, name)
        
        if condition is not None:
            self.conditional_routes.append(route)
        else:
            self.routes.append(route)
            # Add to Trie if static route
            self.static_trie.add(path, route)
    
    def find_route(
        self, path: str, method: str, request: Any = None
    ) -> Optional[Tuple[Route, Dict[str, str]]]:
        """
        Find matching route with optimized lookup.
        
        Args:
            path: Request path
            method: HTTP method
            request: Request object
            
        Returns:
            Tuple of (Route, path_params) if found, None otherwise
        """
        # First try conditional routes (must check all due to conditions)
        for route in self.conditional_routes:
            params = route.match(path, method, request)
            if params is not None:
                return route, params
        
        # Try fast Trie lookup for static routes
        static_route = self.static_trie.find(path)
        if static_route is not None:
            params = static_route.match(path, method, request)
            if params is not None:
                return static_route, params
        
        # Fallback to linear search for routes with parameters
        for route in self.routes:
            # Skip if already checked via Trie
            if "{" not in route.path and "}" not in route.path:
                continue
            params = route.match(path, method, request)
            if params is not None:
                return route, params
        
        return None


def route(
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
        
    Example:
        ```python
        @route("/users/{id}", methods=["GET"])
        def get_user(id: int):
            return {"id": id}
        ```
    """
    def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
        handler._route_path = path
        handler._route_methods = methods or ["GET"]
        handler._route_condition = condition
        handler._route_name = name
        return handler
    
    return decorator


def when(condition: Callable[[Any], bool]):
    """
    Conditional route decorator.
    
    Args:
        condition: Condition function that takes request and returns bool
        
    Example:
        ```python
        @when(lambda req: req.headers.get("X-Client") == "mobile")
        def mobile_handler(request):
            return {"mobile": True}
        ```
    """
    def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
        handler._route_condition = condition
        return handler
    
    return decorator
