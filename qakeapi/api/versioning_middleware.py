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

        # Return default version
        return self.version_manager.default_version

    def _extract_path_version(self, request) -> Optional[str]:
        """Extract version from URL path (e.g., /v1/users)."""
        path = request.path
        parts = path.strip("/").split("/")

        if len(parts) > 0 and parts[0].startswith("v"):
            version_str = parts[0][1:]  # Remove 'v' prefix
            if self.version_manager.is_valid_version(version_str):
                return version_str

        return None

    def _extract_header_version(self, request) -> Optional[str]:
        """Extract version from custom header."""
        version_header = self.version_manager.version_header
        if version_header:
            version_str = request.headers.get(version_header.lower())
            if version_str and self.version_manager.is_valid_version(version_str):
                return version_str

        return None

    def _extract_query_version(self, request) -> Optional[str]:
        """Extract version from query parameter."""
        version_param = self.version_manager.version_param
        if version_param:
            query_params = request.query_params
            if version_param in query_params:
                version_str = query_params[version_param]
                if isinstance(version_str, list):
                    version_str = version_str[0]
                if version_str and self.version_manager.is_valid_version(version_str):
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
        version_header = self.version_manager.version_header or "API-Version"
        response.headers.append(
            (
                version_header.encode()
                if isinstance(version_header, str)
                else version_header,
                version.encode(),
            )
        )

        # Add version status header
        status = self.version_manager.get_version_status(version)
        if status:
            status_header = f"{version_header}-Status"
            response.headers.append(
                (
                    status_header.encode()
                    if isinstance(status_header, str)
                    else status_header,
                    status.value.encode(),
                )
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

    async def __call__(self, request, handler):
        """Route request based on version."""
        version = (
            getattr(request, "api_version", None)
            or self.version_manager.default_version
        )

        # Check if version-specific route exists
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
