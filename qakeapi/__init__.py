"""
QakeAPI - Modern asynchronous web framework for Python

All methods are implemented independently, using only Python standard library.
"""

__version__ = "1.1.0"
__author__ = "QakeAPI Team"
__description__ = "Modern asynchronous web framework for Python"

# Core imports
from .core import (
    QakeAPI,
    Request,
    Response,
    JSONResponse,
    HTMLResponse,
    TextResponse,
    RedirectResponse,
    FileResponse,
    HTTPException,
    FrameworkException,
    BadRequest,
    Unauthorized,
    Forbidden,
    NotFound,
    MethodNotAllowed,
    Conflict,
    InternalServerError,
    Router,
    APIRouter,
    BaseMiddleware,
    Depends,
    WebSocket,
)

# Validation imports
from .validation import (
    BaseModel,
    Field,
    ValidationError,
    StringValidator,
    IntegerValidator,
    FloatValidator,
    BooleanValidator,
    EmailValidator,
    URLValidator,
    DateTimeValidator,
)

# Caching imports
from .caching import (
    MemoryCache,
    CacheManager,
    CacheMiddleware,
)

# Utils imports
from .utils import (
    StaticFiles,
    mount_static,
    TemplateEngine,
    TemplateRenderer,
)

# Testing imports
from .testing import (
    TestClient,
    TestResponse,
    WebSocketTestClient,
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
