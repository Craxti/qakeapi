"""
QakeAPI - Modern asynchronous web framework for Python

🚀 Key Features:
- ⚡ Asynchronous request processing
- 🔍 Automatic data validation
- 🔧 Built-in middleware system
- 🌐 WebSocket support
- 💉 Dependency Injection
- 📚 Automatic OpenAPI documentation generation
- 📁 Static files and templates support
- 📊 Built-in monitoring and metrics
- 🛡️ Advanced security system
- 🏥 Health checks and readiness probes
- 🔄 Database connection pooling
- 🎯 CLI development tools
- 🐛 Centralized error handling
"""

__version__ = "1.1.0"

# Core components
from .core.application import QakeAPI
from .core.request import Request
from .core.response import (
    Response,
    JSONResponse,
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
    FileResponse,
)
from .core.router import APIRouter
from .core.exceptions import HTTPException, QakeAPIException
from .core.dependencies import Depends
from .core.websocket import WebSocket
from .core.error_handling import ErrorHandler
from .config.settings import Settings

# Middleware
from .middleware.cors import CORSMiddleware
from .middleware.logging import LoggingMiddleware, AccessLogMiddleware
from .middleware.auth import AuthMiddleware
from .middleware.compression import CompressionMiddleware

# Monitoring and health (optional)
try:
    from .monitoring.metrics import MetricsCollector, MetricsMiddleware
    from .monitoring.health import (
        HealthChecker,
        HealthCheckMiddleware,
        DatabaseHealthCheck,
        RedisHealthCheck,
        DiskSpaceHealthCheck,
        MemoryHealthCheck,
    )

    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

    # Stubs
    class MetricsCollector:
        pass

    class MetricsMiddleware:
        pass

    class HealthChecker:
        pass

    class HealthCheckMiddleware:
        pass

    class DatabaseHealthCheck:
        pass

    class RedisHealthCheck:
        pass

    class DiskSpaceHealthCheck:
        pass

    class MemoryHealthCheck:
        pass


# Security (optional)
try:
    from .security.auth import JWTManager, PasswordManager, SecurityConfig
    from .security.rate_limiting import RateLimiter, RateLimitMiddleware, RateLimitRule
    from .security.validation import SecurityValidator

    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

    # Stubs
    class JWTManager:
        pass

    class PasswordManager:
        pass

    class SecurityConfig:
        pass

    class RateLimiter:
        pass

    class RateLimitMiddleware:
        pass

    class RateLimitRule:
        pass

    class SecurityValidator:
        pass


# Caching (optional)
try:
    from .caching.cache import CacheManager, InMemoryCache
    from .caching.middleware import CacheMiddleware

    CACHING_AVAILABLE = True
except ImportError:
    CACHING_AVAILABLE = False

    # Stubs
    class CacheManager:
        pass

    class InMemoryCache:
        pass

    class CacheMiddleware:
        pass


# Utils
from .utils.status import status
from .utils.validation import (
    DataValidator,
    StringValidator,
    IntegerValidator,
    FloatValidator,
    BooleanValidator,
    EmailValidator,
    URLValidator,
    DateTimeValidator,
    ListValidator,
    DictValidator,
    validate_json,
)
from .utils.static import StaticFiles
from .utils.templates import TemplateRenderer

# Error handling (опцandонально)
try:
    from .core.error_handling import ErrorHandler, create_error_handler

    ERROR_HANDLING_AVAILABLE = True
except ImportError:
    ERROR_HANDLING_AVAILABLE = False

    # Stubs
    class ErrorHandler:
        pass

    def create_error_handler(*args, **kwargs):
        return ErrorHandler()


__version__ = "1.1.0"
__author__ = "QakeAPI Team"
__description__ = "Соinременный асandнхронный inеб-фреймinорк for Python"
__url__ = "https://github.com/qakeapi/qakeapi"

__all__ = [
    # Core components
    "QakeAPI",
    "Request",
    "Response",
    "JSONResponse",
    "HTMLResponse",
    "PlainTextResponse",
    "RedirectResponse",
    "FileResponse",
    "APIRouter",
    "HTTPException",
    "QakeAPIException",
    "Depends",
    "WebSocket",
    # Middleware
    "CORSMiddleware",
    "LoggingMiddleware",
    "AccessLogMiddleware",
    "AuthMiddleware",
    "CompressionMiddleware",
    # Monitoring
    "MetricsCollector",
    "MetricsMiddleware",
    "HealthChecker",
    "HealthCheckMiddleware",
    "DatabaseHealthCheck",
    "RedisHealthCheck",
    "DiskSpaceHealthCheck",
    "MemoryHealthCheck",
    # Security
    "JWTManager",
    "PasswordManager",
    "RateLimiter",
    "RateLimitMiddleware",
    "SecurityValidator",
    # Caching
    "CacheManager",
    "CacheMiddleware",
    # Utils
    "status",
    "StaticFiles",
    "TemplateRenderer",
    # Валandдацandя
    "DataValidator",
    "StringValidator",
    "IntegerValidator",
    "FloatValidator",
    "BooleanValidator",
    "EmailValidator",
    "URLValidator",
    "DateTimeValidator",
    "ListValidator",
    "DictValidator",
    "validate_json",
    # Error handling
    "ErrorHandler",
    "create_error_handler",
]
