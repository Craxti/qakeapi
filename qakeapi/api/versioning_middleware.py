"""
API Versioning Middleware for QakeAPI.

Provides middleware integration for the versioning system.
"""

import json
import logging
from datetime import date
from typing import Any, Callable, Dict, Optional
from urllib.parse import parse_qs

from .versioning import (
    APIVersionManager,
    DeprecationWarning,
    VersionStatus,
    VersionStrategy,
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
                    "message": "This API version is no longer available",
                },
            )

        # Process request
        response = await handler(request)

        # Add version headers to response
        self._add_version_headers(response, version)

        # Add deprecation warning headers if needed
        if hasattr(request, "deprecation_warning") and request.deprecation_warning:
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

        # Return default version using extract_version
        return self.version_manager.extract_version(request)

    def _extract_path_version(self, request) -> Optional[str]:
        """Extract version from URL path (e.g., /v1/users)."""
        path = request.path
        parts = path.strip("/").split("/")

        if len(parts) > 0 and parts[0].startswith("v"):
            version_str = parts[0]
            version_info = self.version_manager.get_version_info(version_str)
            if version_info:
                return version_str

        return None

    def _extract_header_version(self, request) -> Optional[str]:
        """Extract version from custom header."""
        headers = getattr(request, "headers", {})
        if isinstance(headers, dict):
            # Try common version headers
            for header_name in ["accept-version", "api-version", "version"]:
                version_str = headers.get(header_name)
                if version_str:
                    version_info = self.version_manager.get_version_info(version_str)
                    if version_info:
                        return version_str
        return None

    def _extract_query_version(self, request) -> Optional[str]:
        """Extract version from query parameter."""
        query_params = getattr(request, "query_params", {})
        if not isinstance(query_params, dict):
            # Try to parse from query_string if available
            query_string = getattr(request, "query_string", None)
            if query_string:
                if isinstance(query_string, bytes):
                    query_string = query_string.decode()
                from urllib.parse import parse_qs
                parsed = parse_qs(query_string)
                query_params = {k: v[0] if v else None for k, v in parsed.items()}
            else:
                return None
        for param_name in ["version", "api_version", "v"]:
            if param_name in query_params:
                version_str = query_params[param_name]
                if isinstance(version_str, list):
                    version_str = version_str[0]
                if version_str:
                    version_info = self.version_manager.get_version_info(version_str)
                    if version_info:
                        return version_str
        return None

    def _add_version_headers(self, response, version: str):
        """Add version information to response headers."""
        if not hasattr(response, "headers"):
            response.headers = {}

        # Convert headers to list of tuples if needed
        if isinstance(response.headers, dict):
            headers_list = [
                (
                    k.encode() if isinstance(k, str) else k,
                    v.encode() if isinstance(v, str) else v,
                )
                for k, v in response.headers.items()
            ]
            response.headers = headers_list

        # Add API version header
        version_header = "API-Version"
        response.headers.append((version_header.encode(), version.encode()))

        # Add version status header
        version_info = self.version_manager.get_version_info(version)
        if version_info:
            status_header = "API-Version-Status"
            response.headers.append(
                (status_header.encode(), version_info.status.value.encode())
            )

    def _add_deprecation_headers(self, response, warning: DeprecationWarning):
        """Add deprecation warning headers to response."""
        if not hasattr(response, "headers"):
            response.headers = []

        # Ensure headers is a list
        if isinstance(response.headers, dict):
            headers_list = [
                (
                    k.encode() if isinstance(k, str) else k,
                    v.encode() if isinstance(v, str) else v,
                )
                for k, v in response.headers.items()
            ]
            response.headers = headers_list

        # Add deprecation warning header
        warning_header = "API-Deprecation-Warning"
        response.headers.append((warning_header.encode(), warning.message.encode()))

        # Add sunset date if available
        if warning.sunset_date:
            sunset_header = "API-Sunset-Date"
            sunset_str = (
                warning.sunset_date.isoformat()
                if hasattr(warning.sunset_date, "isoformat")
                else str(warning.sunset_date)
            )
            response.headers.append((sunset_header.encode(), sunset_str.encode()))

        # Add migration guide if available
        if warning.migration_guide:
            migration_header = "API-Migration-Guide"
            response.headers.append(
                (migration_header.encode(), warning.migration_guide.encode())
            )


class VersionRouteMiddleware:
    """Middleware for version-based route routing."""

    def __init__(self, version_manager: APIVersionManager):
        self.version_manager = version_manager
        self.version_routes: Dict[str, Dict[str, Callable]] = {}

    def register_version_route(self, version: str, path: str, handler: Callable):
        """Register a version-specific route."""
        if version not in self.version_routes:
            self.version_routes[version] = {}
        self.version_routes[version][path] = handler

    async def __call__(self, request, handler):
        """Route request based on version."""
        # Get version from request or extract from path
        version = getattr(request, "api_version", None)
        path = request.path
        
        if not version:
            # Try to extract from path
            if path.startswith("/v") and len(path) > 2:
                # Extract version from path (e.g., /v1/users -> v1)
                parts = path[1:].split("/", 1)
                if parts[0].startswith("v") and len(parts[0]) > 1:
                    potential_version = parts[0]
                    # Check if this version is registered
                    if potential_version in self.version_routes:
                        version = potential_version
            if not version:
                version = getattr(self.version_manager, "default_version", "v1")

        # Check if version-specific route exists
        if version and version in self.version_routes:
            # Remove version prefix if present (e.g., /v1/users -> /users)
            version_prefix = f"/{version}"
            if path.startswith(version_prefix):
                # Remove version prefix
                path = path[len(version_prefix):]
                # Ensure path starts with /
                if not path:
                    path = "/"
                elif not path.startswith("/"):
                    path = "/" + path
                
                # Check exact path match
                if path in self.version_routes[version]:
                    return await self.version_routes[version][path](request)

        # Check if versioned path exists
        versioned_path = self._get_versioned_path(request.path, version)
        if versioned_path and versioned_path != request.path:
            # Update request path for versioned route
            request.path = versioned_path

        return await handler(request)

    def _get_versioned_path(self, path: str, version: str) -> Optional[str]:
        """Get versioned path for given path and version."""
        # Simple implementation - can be extended
        if path.startswith("/api/"):
            return f"/api/v{version}{path[4:]}"
        elif not path.startswith(f"/v{version}"):
            return f"/v{version}{path}"

        return None


class VersionCompatibilityMiddleware:
    """Middleware for checking version compatibility."""

    def __init__(self, version_manager: APIVersionManager):
        self.version_manager = version_manager

    async def __call__(self, request, handler):
        """Check version compatibility."""
        client_version = getattr(request, "api_version", "v1")
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
                    "message": "Client and server versions are not compatible",
                },
            )

        return await handler(request)


class VersionAnalyticsMiddleware:
    """Middleware for collecting version usage analytics."""

    def __init__(self, version_manager: APIVersionManager):
        self.version_manager = version_manager
        self.usage_stats: Dict[str, int] = {}

    async def __call__(self, request, handler):
        """Collect version usage statistics."""
        version = getattr(request, "api_version", "v1")

        # Update usage statistics
        self.usage_stats[version] = self.usage_stats.get(version, 0) + 1

        # Log version usage
        logger.info(
            f"API version {version} used for request to {getattr(request, 'path', '')}"
        )

        response = await handler(request)

        # Add usage statistics to response headers
        if hasattr(response, "headers"):
            if isinstance(response.headers, dict):
                response.headers["X-API-Usage-Count"] = str(self.usage_stats[version])
            elif isinstance(response.headers, list):
                response.headers.append(
                    (b"X-API-Usage-Count", str(self.usage_stats[version]).encode())
                )

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
    def create_versioning_middleware(
        version_manager: APIVersionManager,
    ) -> VersioningMiddleware:
        """Create versioning middleware."""
        return VersioningMiddleware(version_manager)

    @staticmethod
    def create_route_middleware(
        version_manager: APIVersionManager,
    ) -> VersionRouteMiddleware:
        """Create version route middleware."""
        return VersionRouteMiddleware(version_manager)

    @staticmethod
    def create_compatibility_middleware(
        version_manager: APIVersionManager,
    ) -> VersionCompatibilityMiddleware:
        """Create version compatibility middleware."""
        return VersionCompatibilityMiddleware(version_manager)

    @staticmethod
    def create_analytics_middleware(
        version_manager: APIVersionManager,
    ) -> VersionAnalyticsMiddleware:
        """Create version analytics middleware."""
        return VersionAnalyticsMiddleware(version_manager)

    @staticmethod
    def create_full_versioning_stack(version_manager: APIVersionManager) -> list:
        """Create full versioning middleware stack."""
        return [
            VersioningMiddleware(version_manager),
            VersionRouteMiddleware(version_manager),
            VersionCompatibilityMiddleware(version_manager),
            VersionAnalyticsMiddleware(version_manager),
        ]
