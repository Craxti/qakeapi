"""
Core components of QakeAPI framework.
"""

from .app import QakeAPI
from .background import BackgroundTask, BackgroundTaskManager, add_background_task, background_task
from .exceptions import (
    HTTPException,
    ValidationError as HTTPValidationError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    InternalServerError,
    PayloadTooLargeError,
)
from .hybrid import hybrid_executor, sync_to_async, run_hybrid
from .logging import QakeAPILogger, get_logger, configure_logging
from .middleware import BaseMiddleware, MiddlewareStack, CORSMiddleware, LoggingMiddleware, RequestSizeLimitMiddleware
from .rate_limit import rate_limit, get_rate_limiter, RateLimiter
from .caching import cache, get_cache, Cache, generate_cache_key
from .reactive import react, Event, EventBus, emit
from .pipeline import pipeline, Pipeline, pipeline_decorator
from .parallel import parallel, ParallelResolver, resolve_parallel
from .router import when, route, Router, Route
from .request import Request
from .response import Response, JSONResponse, HTMLResponse, TextResponse
from .validation import (
    validate_model,
    validate_request_body,
    validate_query_param,
    validate_path_param,
    BaseValidator,
)
from .websocket import WebSocket, WebSocketRoute
from .dependencies import Dependency, Depends
from .files import FileUpload, parse_multipart, IMAGE_TYPES, DOCUMENT_TYPES, IMAGE_MIME_TYPES, DOCUMENT_MIME_TYPES

__all__ = [
    "QakeAPI",
    "hybrid_executor",
    "sync_to_async",
    "run_hybrid",
    "react",
    "Event",
    "EventBus",
    "emit",
    "pipeline",
    "Pipeline",
    "pipeline_decorator",
    "parallel",
    "ParallelResolver",
    "resolve_parallel",
    "when",
    "route",
    "Router",
    "Route",
    "Request",
    "Response",
    "JSONResponse",
    "HTMLResponse",
    "TextResponse",
    "BaseMiddleware",
    "MiddlewareStack",
    "CORSMiddleware",
    "LoggingMiddleware",
    "RequestSizeLimitMiddleware",
    # Logging
    "QakeAPILogger",
    "get_logger",
    "configure_logging",
    # Rate Limiting
    "rate_limit",
    "get_rate_limiter",
    "RateLimiter",
    # Caching
    "cache",
    "get_cache",
    "Cache",
    "generate_cache_key",
    "WebSocket",
    "WebSocketRoute",
    "BackgroundTask",
    "BackgroundTaskManager",
    "add_background_task",
    "background_task",
    # Exceptions
    "HTTPException",
    "HTTPValidationError",
    "NotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
    "InternalServerError",
    "PayloadTooLargeError",
    # Validation
    "validate_model",
    "validate_request_body",
    "validate_query_param",
    "validate_path_param",
    "BaseValidator",
    # Dependency Injection
    "Dependency",
    "Depends",
    # File Upload
    "FileUpload",
    "parse_multipart",
    "IMAGE_TYPES",
    "DOCUMENT_TYPES",
    "IMAGE_MIME_TYPES",
    "DOCUMENT_MIME_TYPES",
]
