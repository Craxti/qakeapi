"""Middleware for API versioning."""

import logging
from typing import Optional, Callable, Any
from .versioning import APIVersionManager, VersionStrategy

logger = logging.getLogger(__name__)

class APIVersioningMiddleware:
    """Middleware for automatic API version detection and routing."""
    
    def __init__(self, version_manager: APIVersionManager):
        self.version_manager = version_manager
        logger.debug("Initialized APIVersioningMiddleware")
    
    async def __call__(self, request: Any, call_next: Callable) -> Any:
        """Process request with version detection."""
        # Extract version from request
        version = self.version_manager.get_version_from_request(request)
        
        # Add version to request context
        request.api_version = version
        
        # Check if version is deprecated
        if self.version_manager.is_version_deprecated(version):
            logger.warning(f"Using deprecated API version: {version}")
            # Add deprecation warning header
            if hasattr(request, 'add_header'):
                request.add_header('X-API-Deprecation', f"Version {version} is deprecated")
        
        # Process request
        response = await call_next(request)
        
        # Add version info to response headers
        if hasattr(response, 'headers'):
            response.headers.append((b'X-API-Version', version.encode()))
            response.headers.append((b'X-API-Supported-Versions', 
                                   ','.join(self.version_manager.get_supported_versions()).encode()))
        
        return response

def version_middleware(version_manager: APIVersionManager):
    """Decorator for adding versioning middleware."""
    def decorator(app: Any) -> Any:
        middleware = APIVersioningMiddleware(version_manager)
        app.add_middleware(middleware)
        return app
    return decorator 