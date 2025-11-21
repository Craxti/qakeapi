"""
QakeAPI - Modern asynchronous web framework for Python

All methods are implemented independently, using only Python standard library.
"""

__version__ = "1.1.0"
__author__ = "QakeAPI Team"
__description__ = "Modern asynchronous web framework for Python"

# Caching imports
from .caching import CacheManager, CacheMiddleware, MemoryCache

# Core imports
from .core import (
    APIRouter,
    BadRequest,
    BaseMiddleware,
    Conflict,
    Depends,
    FileResponse,
    Forbidden,
    FrameworkException,
    HTMLResponse,
    HTTPException,
    InternalServerError,
    JSONResponse,
    MethodNotAllowed,
    NotFound,
    QakeAPI,
    RedirectResponse,
    Request,
    Response,
    Router,
    TextResponse,
    Unauthorized,
    WebSocket,
)

# Testing imports
from .testing import TestClient, TestResponse, WebSocketTestClient

# Utils imports
from .utils import StaticFiles, TemplateEngine, TemplateRenderer, mount_static

# Validation imports
from .validation import (
    BaseModel,
    BooleanValidator,
    DateTimeValidator,
    EmailValidator,
    Field,
    FloatValidator,
    IntegerValidator,
    StringValidator,
    URLValidator,
    ValidationError,
)

__all__ = [
    # Application
    "QakeAPI",
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
    # Dependencies
    "Depends",
    # WebSocket
    "WebSocket",
    # Validation
    "BaseModel",
    "Field",
    "ValidationError",
    "StringValidator",
    "IntegerValidator",
    "FloatValidator",
    "BooleanValidator",
    "EmailValidator",
    "URLValidator",
    "DateTimeValidator",
    # Caching
    "MemoryCache",
    "CacheManager",
    "CacheMiddleware",
    # Utils
    "StaticFiles",
    "mount_static",
    "TemplateEngine",
    "TemplateRenderer",
    # Testing
    "TestClient",
    "TestResponse",
    "WebSocketTestClient",
]
