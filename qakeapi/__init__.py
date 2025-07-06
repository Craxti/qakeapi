"""QakeAPI - Modern async web framework for Python."""

from .core.application import Application
from .core.requests import Request
from .core.responses import Response
from .core.websockets import WebSocketConnection as WebSocket
from .core.routing import (
    HTTPRouter,
    WebSocketRouter,
    MiddlewareManager,
    BaseRoute,
    BaseRouter
)

__version__ = "1.0.3"
__author__ = "QakeAPI Team"

__all__ = [
    "Application",
    "Request", 
    "Response",
    "WebSocket",
    "HTTPRouter",
    "WebSocketRouter", 
    "MiddlewareManager",
    "BaseRoute",
    "BaseRouter"
]
