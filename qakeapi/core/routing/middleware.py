"""Middleware management for routing."""
import logging
from typing import Any, Callable, List
import asyncio

logger = logging.getLogger(__name__)

class MiddlewareManager:
    """Manager for middleware chains."""
    
    def __init__(self):
        self._middleware: List[Callable] = []
        logger.debug("Initialized middleware manager")
    
    def add(self, middleware: Callable) -> None:
        """Add middleware to chain."""
        name = getattr(middleware, '__name__', type(middleware).__name__)
        self._middleware.append(middleware)
        logger.debug(f"Added middleware: {name}")
    
    def apply(self, handler: Callable) -> Callable:
        """Apply middleware chain to handler."""
        for middleware in reversed(self._middleware):
            if asyncio.iscoroutinefunction(middleware):
                prev_handler = handler
                async def wrapped_handler(request: Any, prev_handler=prev_handler):
                    return await middleware(request, prev_handler)
                handler = wrapped_handler
            else:
                handler = middleware(handler)
            logger.debug(f"Applied middleware: {middleware.__name__}")
        return handler
    
    def decorator(self) -> Callable:
        """Decorator for adding middleware."""
        def decorator(middleware: Callable) -> Callable:
            self.add(middleware)
            return middleware
        return decorator
    
    def clear(self) -> None:
        """Clear all middleware."""
        self._middleware.clear()
        logger.debug("Cleared all middleware") 