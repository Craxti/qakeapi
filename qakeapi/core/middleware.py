"""
Middleware system for request/response processing.

This module provides the base middleware class and middleware chain management.
"""

from typing import Any, Callable, Dict, List, Optional
from abc import ABC, abstractmethod


class BaseMiddleware(ABC):
    """
    Base class for middleware.
    
    Middleware can process requests before and after handler execution.
    """
    
    def __init__(self, app: Any = None):
        """
        Initialize middleware.
        
        Args:
            app: ASGI application to wrap
        """
        self.app = app
    
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
        if scope["type"] == "http":
            await self.process_http(scope, receive, send)
        elif scope["type"] == "websocket":
            await self.process_websocket(scope, receive, send)
        else:
            if self.app:
                await self.app(scope, receive, send)
    
    async def process_http(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """
        Process HTTP request.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Create a wrapper for send to intercept responses
        async def send_wrapper(message: Dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                # Process response headers
                await self.process_response_headers(scope, message)
            await send(message)
        
        # Process request before handler
        await self.process_request(scope, receive)
        
        # Call next middleware or app
        if self.app:
            await self.app(scope, receive, send_wrapper)
        else:
            await send_wrapper({
                "type": "http.response.start",
                "status": 404,
                "headers": [],
            })
            await send_wrapper({
                "type": "http.response.body",
                "body": b"Not Found",
            })
    
    async def process_websocket(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """
        Process WebSocket connection.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if self.app:
            await self.app(scope, receive, send)
    
    async def process_request(
        self, scope: Dict[str, Any], receive: Any
    ) -> None:
        """
        Process request before handler execution.
        
        Override this method to add request processing logic.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive callable
        """
        pass
    
    async def process_response_headers(
        self, scope: Dict[str, Any], message: Dict[str, Any]
    ) -> None:
        """
        Process response headers before sending.
        
        Override this method to modify response headers.
        
        Args:
            scope: ASGI scope
            message: ASGI response start message
        """
        pass


class MiddlewareStack:
    """
    Stack of middleware to process requests.
    
    Middleware are executed in the order they are added (first added = outermost).
    """
    
    def __init__(self, app: Any):
        """
        Initialize middleware stack.
        
        Args:
            app: Base ASGI application
        """
        self.app = app
        self.middleware: List[BaseMiddleware] = []
    
    def add(self, middleware: BaseMiddleware) -> None:
        """
        Add middleware to stack.
        
        Args:
            middleware: Middleware instance to add
        """
        self.middleware.append(middleware)
    
    async def __call__(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """
        Execute middleware stack.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Build middleware chain
        app = self.app
        
        # Add middleware in reverse order (last added wraps innermost)
        for middleware in reversed(self.middleware):
            middleware.app = app
            app = middleware
        
        # Execute chain
        await app(scope, receive, send)

