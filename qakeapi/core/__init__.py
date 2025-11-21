"""
Core framework components - main application components.
"""

from .application import QakeAPI
from .dependencies import Dependency, Depends, resolve_dependencies
from .exceptions import (
    AuthenticationException,
    AuthorizationException,
    BadRequest,
    Conflict,
    Forbidden,
    FrameworkException,
    HTTPException,
    InternalServerError,
    MethodNotAllowed,
    NotFound,
    QakeAPIException,
    Unauthorized,
    ValidationException,
)
from .middleware_core import BaseMiddleware, MiddlewareStack
from .request import Request
from .response import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
    TextResponse,
)
from .router import APIRouter, Router
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
    "ValidationException",
    "QakeAPIException",
    "AuthenticationException",
    "AuthorizationException",
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
