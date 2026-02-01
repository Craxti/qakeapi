"""
QakeAPI - Revolutionary Hybrid Async/Sync Web Framework for Python.

QakeAPI is a unique web framework that seamlessly supports both
asynchronous and synchronous code, with automatic parallel processing
and reactive routing capabilities.

Key Features:
- Hybrid sync/async execution
- Parallel dependency resolution
- Reactive routing
- Pipeline composition
- Smart conditional routing
- Zero dependencies (core framework)
"""

__version__ = "1.3.0"
__author__ = "QakeAPI Team"
__description__ = "Revolutionary Hybrid Async/Sync Web Framework"

# Core imports
from .core import (
    QakeAPI,
    hybrid_executor,
    sync_to_async,
    run_hybrid,
    react,
    Event,
    EventBus,
    emit,
    pipeline,
    Pipeline,
    pipeline_decorator,
    parallel,
    ParallelResolver,
    resolve_parallel,
    when,
    route,
    Router,
    Route,
    Request,
    Response,
    JSONResponse,
    HTMLResponse,
    TextResponse,
    BaseMiddleware,
    MiddlewareStack,
    CORSMiddleware,
    LoggingMiddleware,
    RequestSizeLimitMiddleware,
    WebSocket,
    WebSocketRoute,
    BackgroundTask,
    BackgroundTaskManager,
    add_background_task,
    background_task,
    rate_limit,
    get_rate_limiter,
    RateLimiter,
    cache,
    get_cache,
    Cache,
    generate_cache_key,
    Depends,
    Dependency,
    FileUpload,
    IMAGE_TYPES,
    DOCUMENT_TYPES,
    IMAGE_MIME_TYPES,
    DOCUMENT_MIME_TYPES,
    init_auth,
    require_auth,
    require_role,
    create_token,
    decode_token,
    create_session,
    get_session,
    delete_session,
    get_jwt_manager,
    get_session_manager,
    JWTManager,
    SessionManager,
)

__all__ = [
    # Application
    "QakeAPI",
    # Hybrid
    "hybrid_executor",
    "sync_to_async",
    "run_hybrid",
    # Reactive
    "react",
    "Event",
    "EventBus",
    "emit",
    # Pipeline
    "pipeline",
    "Pipeline",
    "pipeline_decorator",
    # Parallel
    "parallel",
    "ParallelResolver",
    "resolve_parallel",
    # Router
    "when",
    "route",
    "Router",
    "Route",
    # Request/Response
    "Request",
    "Response",
    "JSONResponse",
    "HTMLResponse",
    "TextResponse",
    # Middleware
    "BaseMiddleware",
    "MiddlewareStack",
    "CORSMiddleware",
    "LoggingMiddleware",
    "RequestSizeLimitMiddleware",
    # WebSocket
    "WebSocket",
    "WebSocketRoute",
    # Background Tasks
    "BackgroundTask",
    "BackgroundTaskManager",
    "add_background_task",
    "background_task",
    # Rate Limiting
    "rate_limit",
    "get_rate_limiter",
    "RateLimiter",
    # Caching
    "cache",
    "get_cache",
    "Cache",
    "generate_cache_key",
    # Dependency Injection
    "Depends",
    "Dependency",
    # File Upload
    "FileUpload",
    "IMAGE_TYPES",
    "DOCUMENT_TYPES",
    "IMAGE_MIME_TYPES",
    "DOCUMENT_MIME_TYPES",
    # Authentication & Authorization
    "init_auth",
    "require_auth",
    "require_role",
    "create_token",
    "decode_token",
    "create_session",
    "get_session",
    "delete_session",
    "get_jwt_manager",
    "get_session_manager",
    "JWTManager",
    "SessionManager",
]
