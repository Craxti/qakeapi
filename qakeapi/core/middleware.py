"""
Middleware system for QakeAPI.

This module provides middleware functionality for intercepting
and processing requests and responses.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


class BaseMiddleware(ABC):
    """
    Base middleware class.
    
    All middleware should inherit from this class and implement
    the process method.
    """
    
    @abstractmethod
    async def process(
        self,
        request: Any,
        call_next: Callable[..., Any],
    ) -> Any:
        """
        Process request/response.
        
        Args:
            request: Request object
            call_next: Next middleware or handler in chain
            
        Returns:
            Response object
            
        Example:
            ```python
            class LoggingMiddleware(BaseMiddleware):
                async def process(self, request, call_next):
                    print(f"Request: {request.method} {request.path}")
                    response = await call_next(request)
                    print(f"Response: {response.status_code}")
                    return response
            ```
        """
        pass


class MiddlewareStack:
    """
    Middleware stack for processing requests.
    
    Maintains a chain of middleware that process requests
    in order before reaching the handler.
    """
    
    def __init__(self, handler: Callable[..., Any]):
        """
        Initialize middleware stack.
        
        Args:
            handler: Final handler function
        """
        self.handler = handler
        self.middleware: List[BaseMiddleware] = []
    
    def add(self, middleware: BaseMiddleware) -> None:
        """
        Add middleware to stack.
        
        Args:
            middleware: Middleware instance
        """
        self.middleware.append(middleware)
    
    async def __call__(self, request: Any) -> Any:
        """
        Process request through middleware stack.
        
        Args:
            request: Request object
            
        Returns:
            Response object
        """
        # Build middleware chain
        async def run_chain(index: int) -> Any:
            """Run middleware chain recursively."""
            if index >= len(self.middleware):
                # All middleware processed, call handler
                return await self.handler(request)
            
            # Get current middleware
            middleware = self.middleware[index]
            
            # Call next in chain
            async def call_next(req: Any) -> Any:
                return await run_chain(index + 1)
            
            # Process through middleware
            return await middleware.process(request, call_next)
        
        return await run_chain(0)


# Built-in middleware

class CORSMiddleware(BaseMiddleware):
    """CORS middleware for handling Cross-Origin Resource Sharing."""
    
    def __init__(
        self,
        allow_origins: list = None,
        allow_methods: list = None,
        allow_headers: list = None,
    ):
        """
        Initialize CORS middleware.
        
        Args:
            allow_origins: List of allowed origins
            allow_methods: List of allowed methods
            allow_headers: List of allowed headers
        """
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]
    
    async def process(self, request: Any, call_next: Callable[..., Any]) -> Any:
        """Process CORS headers."""
        from .response import Response
        
        # Handle preflight request (OPTIONS)
        if request.method == "OPTIONS":
            from .response import Response as BaseResponse
            response = BaseResponse(status_code=204)
            cors_headers = self._get_cors_headers(request)
            response.headers.update(cors_headers)
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers to ALL responses
        # This is critical - CORS headers must be present on all responses
        cors_headers = self._get_cors_headers(request)
        
        # Always ensure CORS headers are added
        if isinstance(response, Response):
            # Update headers - CORS headers should always be set
            for key, value in cors_headers.items():
                # Always set CORS headers, don't merge
                response.headers[key] = value
        elif hasattr(response, "headers"):
            # For non-Response objects with headers attribute
            for key, value in cors_headers.items():
                response.headers[key] = value
        
        return response
    
    def _get_cors_headers(self, request: Any) -> Dict[str, str]:
        """Get CORS headers."""
        origin = self._extract_origin(request)
        headers = {}
        
        headers["Access-Control-Allow-Origin"] = self._get_allow_origin(origin)
        headers["Access-Control-Allow-Methods"] = self._get_allow_methods()
        headers["Access-Control-Allow-Headers"] = self._get_allow_headers()
        headers["Access-Control-Expose-Headers"] = "Content-Type, Content-Length, Authorization"
        headers["Access-Control-Max-Age"] = "3600"
        
        # Allow credentials only if origin is not "*"
        if headers["Access-Control-Allow-Origin"] != "*":
            headers["Access-Control-Allow-Credentials"] = "true"
        
        return headers
    
    def _extract_origin(self, request: Any) -> str:
        """Extract origin from request headers."""
        origin = request.headers.get("origin", "")
        
        # Try to get origin from referer if origin header is missing
        if not origin:
            referer = request.headers.get("referer", "")
            if referer:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(referer)
                    origin = f"{parsed.scheme}://{parsed.netloc}"
                except Exception:
                    pass
        
        return origin
    
    def _get_allow_origin(self, origin: str) -> str:
        """Get Access-Control-Allow-Origin header value."""
        if "*" in self.allow_origins:
            return origin if origin else "*"
        
        if origin and origin in self.allow_origins:
            return origin
        
        # Default to "*" for same-origin requests or when origin not in allowed list
        return "*"
    
    def _get_allow_methods(self) -> str:
        """Get Access-Control-Allow-Methods header value."""
        if "*" in self.allow_methods:
            return "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD"
        
        methods_str = ", ".join(self.allow_methods)
        if "OPTIONS" not in methods_str:
            methods_str += ", OPTIONS"
        return methods_str
    
    def _get_allow_headers(self) -> str:
        """Get Access-Control-Allow-Headers header value."""
        if "*" in self.allow_headers:
            return "Content-Type, Authorization, Accept, X-Requested-With, Origin, X-CSRFToken"
        
        headers_str = ", ".join(self.allow_headers)
        # Ensure common headers are included
        common_headers = ["Content-Type", "Accept"]
        for hdr in common_headers:
            if hdr not in headers_str:
                headers_str += f", {hdr}"
        return headers_str


class RequestSizeLimitMiddleware(BaseMiddleware):
    """Middleware for validating request body size."""
    
    def __init__(self, max_size: int = 10 * 1024 * 1024):
        """
        Initialize request size limit middleware.
        
        Args:
            max_size: Maximum request body size in bytes (default: 10MB)
        """
        self.max_size = max_size
    
    async def process(self, request: Any, call_next: Callable[..., Any]) -> Any:
        """Validate request body size."""
        from .response import Response
        from .exceptions import PayloadTooLargeError
        
        # Check Content-Length header if present
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    raise PayloadTooLargeError(
                        f"Request body too large: {size} bytes (max: {self.max_size} bytes)"
                    )
            except ValueError:
                # Invalid Content-Length header, continue
                pass
        
        # For streaming requests, check body as it's read
        # This is a best-effort check - actual size might exceed if Content-Length was wrong
        try:
            response = await call_next(request)
            return response
        except PayloadTooLargeError:
            raise
        except Exception as e:
            # Check if body was read and exceeded limit
            if hasattr(request, "_body") and request._body:
                if len(request._body) > self.max_size:
                    raise PayloadTooLargeError(
                        f"Request body too large: {len(request._body)} bytes (max: {self.max_size} bytes)"
                    )
            raise


class LoggingMiddleware(BaseMiddleware):
    """Logging middleware for request/response logging."""
    
    def __init__(self, logger=None):
        """
        Initialize logging middleware.
        
        Args:
            logger: Optional logger instance (uses default if not provided)
        """
        from .logging import get_logger
        self.logger = logger or get_logger()
    
    async def process(self, request: Any, call_next: Callable[..., Any]) -> Any:
        """Log request and response."""
        import time
        
        start_time = time.time()
        client_ip = None
        if hasattr(request, "client") and request.client:
            client_ip = request.client[0] if isinstance(request.client, tuple) else str(request.client)
        
        # Log request
        self.logger.info(
            f"{request.method} {request.path}",
            method=request.method,
            path=request.path,
            client_ip=client_ip,
            extra={"event": "request_start"}
        )
        
        try:
            response = await call_next(request)
            
            process_time = time.time() - start_time
            status_code = getattr(response, "status_code", 200)
            
            # Determine log level based on status code
            if status_code >= 500:
                log_level = "error"
            elif status_code >= 400:
                log_level = "warning"
            else:
                log_level = "info"
            
            # Log response
            getattr(self.logger, log_level)(
                f"{request.method} {request.path} - {status_code} ({process_time:.3f}s)",
                method=request.method,
                path=request.path,
                status_code=status_code,
                process_time=process_time,
                client_ip=client_ip,
                extra={"event": "request_complete"}
            )
            
            return response
        
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log error
            self.logger.error(
                f"{request.method} {request.path} - ERROR ({process_time:.3f}s): {str(e)}",
                method=request.method,
                path=request.path,
                process_time=process_time,
                client_ip=client_ip,
                exc_info=True,
                extra={"event": "request_error"}
            )
            
            raise

