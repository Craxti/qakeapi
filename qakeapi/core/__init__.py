"""
Core framework components - main application components.
"""

from .request import Request
from .response import (
    Response,
    JSONResponse,
    HTMLResponse,
    TextResponse,
    RedirectResponse,
    FileResponse,
)
from .exceptions import (
    HTTPException,
    FrameworkException,
    BadRequest,
    Unauthorized,
    Forbidden,
    NotFound,
    MethodNotAllowed,
    Conflict,
    InternalServerError,
)
from .router import Router, APIRouter
from .middleware_core import BaseMiddleware, MiddlewareStack
from .application import QakeAPI
from .dependencies import Depends, Dependency, resolve_dependencies
from .websocket import WebSocket, WebSocketState

__all__ = [
    # Request/Response
    "Request",
    "Response",
    "JSONResponse",
    "HTMLResponse",
    "TextResponse",
    "RedirectResponse",
    "FileResponse",
    # Exceptions
    "HTTPException",
    "FrameworkException",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "MethodNotAllowed",
    "Conflict",
    "InternalServerError",
    # Router
    "Router",
    "APIRouter",
    # Middleware
    "BaseMiddleware",
    "MiddlewareStack",
    # Application
    "QakeAPI",
    # Dependencies
    "Depends",
    "Dependency",
    "resolve_dependencies",
    # WebSocket
    "WebSocket",
    "WebSocketState",
]
