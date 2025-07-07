"""
API Versioning Middleware for QakeAPI.

Provides middleware integration for the versioning system.
"""

import json
import logging
from datetime import date
from typing import Dict, Any, Optional, Callable
from urllib.parse import parse_qs

from .versioning import (
    APIVersionManager, 
    VersionStrategy, 
    VersionStatus,
    DeprecationWarning
)

logger = logging.getLogger(__name__)


class VersioningMiddleware:
    """Middleware for handling API versioning in QakeAPI applications."""
    
    def __init__(self, version_manager: APIVersionManager):
        self.version_manager = version_manager
    
    async def __call__(self, request, handler):
        """Process request with versioning."""
        # Extract version from request
        version = self._extract_version_from_request(request)
        
        # Add version to request context
        request.api_version = version
        
        # Check for deprecation warnings
        if self.version_manager.is_version_deprecated(version):
            warning = self.version_manager.get_deprecation_warning(version)
            if warning:
                request.deprecation_warning = warning
        
        # Check for sunset
        if self.version_manager.is_version_sunset(version):
            from qakeapi.core.responses import JSONResponse
            return JSONResponse(
                status_code=410,
                content={
                    "error": "API version has been sunset",
                    "version": version,
                    "message": "This API version is no longer available"
                }
            )
        
        # Process request
        response = await handler(request)
        
        # Add version headers to response
        self._add_version_headers(response, version)
        
        # Add deprecation warning headers if needed
        if hasattr(request, 'deprecation_warning') and request.deprecation_warning:
            self._add_deprecation_headers(response, request.deprecation_warning)
        
        return response
    
    def _extract_version_from_request(self, request) -> str:
        """Extract version from request using multiple strategies."""
        # Try path-based versioning first
        path_version = self._extract_path_version(request)
        if path_version:
            return path_version
        
        # Try header-based versioning
        header_version = self._extract_header_version(request)
        if header_version:
            return header_version
        
        # Try query parameter versioning
        query_version = self._extract_query_version(request)
        if query_version:
            return query_version
        
        # Return default version
        return self.version_manager.extract_version(request)
    
    def _extract_path_version(self, request) -> Optional[str]:
        """Extract version from URL path."""
        path = getattr(request, 'path', '')
        import re
        match = re.match(r'^/v(\d+)/', path)
        if match:
            version = f"v{match.group(1)}"
            if self.version_manager.get_version_info(version):
                return version
        return None
    
    def _extract_header_version(self, request) -> Optional[str]:
        """Extract version from Accept-Version header."""
        headers = getattr(request, 'headers', {})
        version_header = headers.get('accept-version', '')
        
        if version_header:
            # Parse Accept-Version header (e.g., "v1, v2;q=0.9")
            versions = [v.strip().split(';')[0] for v in version_header.split(',')]
            for version in versions:
                if self.version_manager.get_version_info(version):
                    return version
        
        return None
    
    def _extract_query_version(self, request) -> Optional[str]:
        """Extract version from query parameters."""
        query_string = getattr(request, 'query_string', b'').decode()
        if query_string:
            query_params = parse_qs(query_string)
            version = query_params.get('version', [None])[0]
            if version and self.version_manager.get_version_info(version):
                return version
        return None
    
    def _add_version_headers(self, response, version: str):
        """Add version headers to response."""
        if hasattr(response, 'headers'):
            response.headers['X-API-Version'] = version
            response.headers['X-API-Version-Status'] = self._get_version_status(version)
    
    def _add_deprecation_headers(self, response, warning: DeprecationWarning):
        """Add deprecation warning headers to response."""
        if hasattr(response, 'headers'):
            response.headers['X-API-Deprecation'] = 'true'
            response.headers['X-API-Deprecation-Message'] = warning.message
            response.headers['X-API-Deprecation-Date'] = warning.deprecation_date.isoformat()
            
            if warning.sunset_date:
                response.headers['X-API-Sunset-Date'] = warning.sunset_date.isoformat()
            
            if warning.alternative_endpoint:
                response.headers['X-API-Alternative-Endpoint'] = warning.alternative_endpoint
    
    def _get_version_status(self, version: str) -> str:
        """Get version status string."""
        version_info = self.version_manager.get_version_info(version)
        if version_info:
            return version_info.status.value
        return 'unknown'


class VersionRouteMiddleware:
    """Middleware for handling version-specific routes."""
    
    def __init__(self, version_manager: APIVersionManager):
        self.version_manager = version_manager
        self.version_routes: Dict[str, Dict[str, Callable]] = {}
    
    def register_version_route(self, version: str, path: str, handler: Callable):
        """Register a route for a specific version."""
        if version not in self.version_routes:
            self.version_routes[version] = {}
        self.version_routes[version][path] = handler
    
    async def __call__(self, request, handler):
        """Process request with version-specific routing."""
        version = getattr(request, 'api_version', 'v1')
        
        # Check if there's a version-specific route
        if version in self.version_routes:
            path = getattr(request, 'path', '')
            # Remove version prefix from path for route matching
            clean_path = self._remove_version_prefix(path, version)
            
            if clean_path in self.version_routes[version]:
                # Use version-specific handler
                return await self.version_routes[version][clean_path](request)
        
        # Use default handler
        return await handler(request)
    
    def _remove_version_prefix(self, path: str, version: str) -> str:
        """Remove version prefix from path."""
        import re
        return re.sub(r'^/v\d+/', '/', path)


class VersionCompatibilityMiddleware:
    """Middleware for checking version compatibility."""
    
    def __init__(self, version_manager: APIVersionManager):
        self.version_manager = version_manager
    
    async def __call__(self, request, handler):
        """Check version compatibility."""
        client_version = getattr(request, 'api_version', 'v1')
        all_versions = self.version_manager.get_all_versions()
        
        if not all_versions:
            return await handler(request)
        
        server_version = all_versions[-1]  # Latest version
        
        if not self.version_manager.is_compatible(client_version, server_version):
            from qakeapi.core.responses import JSONResponse
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Version compatibility error",
                    "client_version": client_version,
                    "server_version": server_version,
                    "message": "Client and server versions are not compatible"
                }
            )
        
        return await handler(request)


class VersionAnalyticsMiddleware:
    """Middleware for collecting version usage analytics."""
    
    def __init__(self, version_manager: APIVersionManager):
        self.version_manager = version_manager
        self.usage_stats: Dict[str, int] = {}
    
    async def __call__(self, request, handler):
        """Collect version usage statistics."""
        version = getattr(request, 'api_version', 'v1')
        
        # Update usage statistics
        self.usage_stats[version] = self.usage_stats.get(version, 0) + 1
        
        # Log version usage
        logger.info(f"API version {version} used for request to {getattr(request, 'path', '')}")
        
        response = await handler(request)
        
        # Add usage statistics to response headers
        if hasattr(response, 'headers'):
            response.headers['X-API-Usage-Count'] = str(self.usage_stats[version])
        
        return response

    def get_usage_stats(self) -> Dict[str, int]:
        """Get version usage statistics."""
        return self.usage_stats.copy()
    
    def reset_stats(self):
        """Reset usage statistics."""
        self.usage_stats.clear()


# Factory for creating versioning middleware
class VersioningMiddlewareFactory:
    """Factory for creating versioning middleware components."""
    
    @staticmethod
    def create_versioning_middleware(version_manager: APIVersionManager) -> VersioningMiddleware:
        """Create versioning middleware."""
        return VersioningMiddleware(version_manager)
    
    @staticmethod
    def create_route_middleware(version_manager: APIVersionManager) -> VersionRouteMiddleware:
        """Create version route middleware."""
        return VersionRouteMiddleware(version_manager)
    
    @staticmethod
    def create_compatibility_middleware(version_manager: APIVersionManager) -> VersionCompatibilityMiddleware:
        """Create version compatibility middleware."""
        return VersionCompatibilityMiddleware(version_manager)
    
    @staticmethod
    def create_analytics_middleware(version_manager: APIVersionManager) -> VersionAnalyticsMiddleware:
        """Create version analytics middleware."""
        return VersionAnalyticsMiddleware(version_manager)
    
    @staticmethod
    def create_full_versioning_stack(version_manager: APIVersionManager) -> list:
        """Create full versioning middleware stack."""
        return [
            VersioningMiddleware(version_manager),
            VersionRouteMiddleware(version_manager),
            VersionCompatibilityMiddleware(version_manager),
            VersionAnalyticsMiddleware(version_manager)
        ] 