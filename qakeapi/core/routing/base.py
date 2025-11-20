"""Base classes for routing."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Pattern, Union
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class RouteMatch:
    """Result of route matching."""
    params: Dict[str, str]
    handler: Callable
    route_info: Any

class BaseRoute(ABC):
    """Base class for routes."""
    
    def __init__(self, path: str, handler: Callable, name: Optional[str] = None):
        self.path = path
        self.handler = handler
        self.name = name
        self.pattern = self._compile_pattern(path)
        logger.debug(f"Created route: {path} {name}")
    
    @abstractmethod
    def _compile_pattern(self, path: str) -> Pattern:
        """Compile path pattern to regex."""
        pass
    
    @abstractmethod
    def match(self, path: str) -> Optional[Dict[str, str]]:
        """Check if path matches route pattern."""
        pass
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(path={self.path}, name={self.name})"

class BaseRouter(ABC):
    """Base class for routers."""
    
    def __init__(self):
        self._routes: List[BaseRoute] = []
        self._middleware: List[Callable] = []
        logger.debug("Initialized router")
    
    @property
    def routes(self) -> List[BaseRoute]:
        """Get routes list."""
        return self._routes
    
    @abstractmethod
    def add_route(self, route: BaseRoute) -> None:
        """Add a route to the router."""
        pass
    
    @abstractmethod
    async def handle_request(self, request: Any) -> Any:
        """Handle incoming request."""
        pass
    
    def add_middleware(self, middleware: Callable) -> None:
        """Add middleware to the router."""
        self._middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__name__}")
    
    def middleware(self) -> Callable:
        """Decorator for adding middleware."""
        def decorator(middleware: Callable) -> Callable:
            self.add_middleware(middleware)
            return middleware
        return decorator
    
    def url_for(self, name: str, **params: Any) -> str:
        """Generate URL for named route."""
        for route in self._routes:
            if hasattr(route, 'name') and route.name == name:
                path = route.path
                for key, value in params.items():
                    path = path.replace(f"{{{key}}}", str(value))
                return path
        raise ValueError(f"No route found with name '{name}')") 