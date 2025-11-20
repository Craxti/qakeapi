"""
Enhanced API Versioning Example Application.

Demonstrates comprehensive API versioning features:
- Multiple versioning strategies (path, header, query)
- Deprecation warnings and sunset dates
- Version compatibility matrix
- Version-specific routes
- Analytics and monitoring
"""

import asyncio
import json
from datetime import date, timedelta
from typing import Dict, Any, List

from qakeapi import QakeAPI
from qakeapi.core.responses import JSONResponse
from qakeapi.api.versioning import (
    APIVersionManager,
    VersionStrategy,
    VersionStatus,
    VersionInfo,
    VersionManagerFactory,
    version_required,
    deprecated_version
)
from qakeapi.api.versioning_middleware import (
    VersioningMiddleware,
    VersionRouteMiddleware,
    VersionCompatibilityMiddleware,
    VersionAnalyticsMiddleware,
    VersioningMiddlewareFactory
)


class EnhancedVersioningApp:
    """Enhanced API versioning example application."""
    
    def __init__(self):
        self.app = QakeAPI(title="Enhanced API Versioning", version="1.0.0")
        self.version_manager = self._setup_version_manager()
        self._setup_middleware()
        self._setup_routes()
        self._setup_version_specific_routes()
    
    def _setup_version_manager(self) -> APIVersionManager:
        """Set up version manager with multiple strategies."""
        # Create multi-strategy manager
        manager = VersionManagerFactory.create_multi_strategy_manager(
            versions=["v1", "v2", "v3"],
            default_version="v1"
        )
        
        # Register version information
        v1_info = VersionInfo(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=date(2023, 1, 1),
            description="Initial API version",
            new_features=["Basic CRUD operations", "Authentication"],
            bug_fixes=[]
        )
        
        v2_info = VersionInfo(
            version="v2",
            status=VersionStatus.ACTIVE,
            release_date=date(2023, 6, 1),
            description="Enhanced API with pagination and filtering",
            breaking_changes=["Changed response format", "Removed deprecated fields"],
            new_features=["Pagination", "Advanced filtering", "Bulk operations"],
            bug_fixes=["Fixed authentication bug", "Improved error handling"]
        )
        
        v3_info = VersionInfo(
            version="v3",
            status=VersionStatus.DEPRECATED,
            release_date=date(2024, 1, 1),
            deprecation_date=date(2024, 6, 1),
            sunset_date=date(2024, 12, 31),
            description="Experimental version with GraphQL-like features",
            breaking_changes=["Complete response format change", "New authentication method"],
            new_features=["GraphQL-like queries", "Real-time subscriptions", "Advanced caching"],
            bug_fixes=["Performance improvements", "Security enhancements"]
        )
        
        manager.register_version(v1_info)
        manager.register_version(v2_info)
        manager.register_version(v3_info)
        
        # Add version compatibility
        manager.add_compatibility("v1", ["v2"])
        manager.add_compatibility("v2", ["v1", "v3"])
        manager.add_compatibility("v3", ["v2"])
        
        return manager
    
    def _setup_middleware(self):
        """Set up versioning middleware stack."""
        # Create middleware components
        versioning_middleware = VersioningMiddlewareFactory.create_versioning_middleware(self.version_manager)
        route_middleware = VersioningMiddlewareFactory.create_route_middleware(self.version_manager)
        compatibility_middleware = VersioningMiddlewareFactory.create_compatibility_middleware(self.version_manager)
        analytics_middleware = VersioningMiddlewareFactory.create_analytics_middleware(self.version_manager)
        
        # Add middleware to app
        self.app.add_middleware(versioning_middleware)
        self.app.add_middleware(route_middleware)
        self.app.add_middleware(compatibility_middleware)
        self.app.add_middleware(analytics_middleware)
        
        # Store analytics middleware for stats access
        self.analytics_middleware = analytics_middleware
    
    def _setup_routes(self):
        """Set up common routes."""
        
        @self.app.get("/")
        async def root(request):
            """Root endpoint with version information."""
            return JSONResponse(content={
                "message": "Enhanced API Versioning Example",
                "current_version": getattr(request, 'api_version', 'v1'),
                "supported_versions": self.version_manager.get_all_versions(),
                "active_versions": self.version_manager.get_active_versions(),
                "deprecated_versions": self.version_manager.get_deprecated_versions()
            })
        
        @self.app.get("/versions")
        async def get_versions(request):
            """Get detailed version information."""
            versions_info = {}
            for version in self.version_manager.get_all_versions():
                info = self.version_manager.get_version_info(version)
                if info:
                    versions_info[version] = {
                        "status": info.status.value,
                        "release_date": info.release_date.isoformat() if info.release_date else None,
                        "deprecation_date": info.deprecation_date.isoformat() if info.deprecation_date else None,
                        "sunset_date": info.sunset_date.isoformat() if info.sunset_date else None,
                        "description": info.description,
                        "breaking_changes": info.breaking_changes,
                        "new_features": info.new_features,
                        "bug_fixes": info.bug_fixes
                    }
            
            return JSONResponse(content={
                "versions": versions_info,
                "compatibility_matrix": self._get_compatibility_matrix()
            })
        
        @self.app.get("/compatibility")
        async def check_compatibility(request):
            """Check version compatibility."""
            client_version = getattr(request, 'api_version', 'v1')
            server_versions = self.version_manager.get_all_versions()
            
            compatibility = {}
            for server_version in server_versions:
                compatibility[server_version] = self.version_manager.is_compatible(
                    client_version, server_version
                )
            
            return JSONResponse(content={
                "client_version": client_version,
                "compatibility": compatibility
            })
        
        @self.app.get("/analytics")
        async def get_analytics(request):
            """Get version usage analytics."""
            stats = self.analytics_middleware.get_usage_stats()
            total_requests = sum(stats.values())
            
            analytics = {
                "total_requests": total_requests,
                "version_usage": stats,
                "usage_percentage": {
                    version: (count / total_requests * 100) if total_requests > 0 else 0
                    for version, count in stats.items()
                }
            }
            
            return JSONResponse(content=analytics)
        
        @self.app.post("/analytics/reset")
        async def reset_analytics(request):
            """Reset analytics data."""
            self.analytics_middleware.reset_stats()
            return JSONResponse(content={"message": "Analytics reset successfully"})
        
        @self.app.get("/users")
        async def get_users(request):
            """Get users with version-specific behavior."""
            version = getattr(request, 'api_version', 'v1')
            
            if version == "v1":
                return JSONResponse(content={
                    "users": [
                        {"id": 1, "name": "John Doe", "email": "john@example.com"},
                        {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
                    ]
                })
            elif version == "v2":
                return JSONResponse(content={
                    "users": [
                        {"id": 1, "name": "John Doe", "email": "john@example.com", "created_at": "2023-01-01"},
                        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "created_at": "2023-01-02"}
                    ],
                    "pagination": {
                        "page": 1,
                        "per_page": 10,
                        "total": 2
                    }
                })
            else:  # v3
                return JSONResponse(content={
                    "data": {
                        "users": [
                            {"id": 1, "name": "John Doe", "email": "john@example.com", "created_at": "2023-01-01", "status": "active"},
                            {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "created_at": "2023-01-02", "status": "active"}
                        ]
                    },
                    "meta": {
                        "pagination": {"page": 1, "per_page": 10, "total": 2},
                        "cached": True,
                        "cache_ttl": 300
                    }
                })
        
        @self.app.get("/users/{user_id}")
        async def get_user(request, user_id: int):
            """Get specific user with version-specific behavior."""
            version = getattr(request, 'api_version', 'v1')
            
            if version == "v1":
                return JSONResponse(content={
                    "id": user_id,
                    "name": f"User {user_id}",
                    "email": f"user{user_id}@example.com"
                })
            elif version == "v2":
                return JSONResponse(content={
                    "id": user_id,
                    "name": f"User {user_id}",
                    "email": f"user{user_id}@example.com",
                    "created_at": "2023-01-01",
                    "updated_at": "2023-06-01"
                })
            else:  # v3
                return JSONResponse(content={
                    "data": {
                        "id": user_id,
                        "name": f"User {user_id}",
                        "email": f"user{user_id}@example.com",
                        "created_at": "2023-01-01",
                        "updated_at": "2023-06-01",
                        "status": "active",
                        "preferences": {"theme": "dark", "language": "en"}
                    },
                    "meta": {
                        "cached": True,
                        "cache_ttl": 300,
                        "last_modified": "2023-06-01T10:00:00Z"
                    }
                })
        
        @self.app.post("/users")
        async def create_user(request):
            """Create user with version-specific validation."""
            version = getattr(request, 'api_version', 'v1')
            body = await request.json()
            
            if version == "v1":
                # Simple validation
                if not body.get("name") or not body.get("email"):
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Name and email are required"}
                    )
                
                return JSONResponse(
                    status_code=201,
                    content={
                        "id": 3,
                        "name": body["name"],
                        "email": body["email"]
                    }
                )
            elif version == "v2":
                # Enhanced validation
                if not body.get("name") or not body.get("email"):
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Name and email are required"}
                    )
                
                # Email validation
                if "@" not in body["email"]:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid email format"}
                    )
                
                return JSONResponse(
                    status_code=201,
                    content={
                        "id": 3,
                        "name": body["name"],
                        "email": body["email"],
                        "created_at": date.today().isoformat()
                    }
                )
            else:  # v3
                # Advanced validation with preferences
                if not body.get("name") or not body.get("email"):
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Name and email are required"}
                    )
                
                # Email validation
                if "@" not in body["email"]:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid email format"}
                    )
                
                return JSONResponse(
                    status_code=201,
                    content={
                        "data": {
                            "id": 3,
                            "name": body["name"],
                            "email": body["email"],
                            "created_at": date.today().isoformat(),
                            "status": "active",
                            "preferences": body.get("preferences", {})
                        },
                        "meta": {
                            "created_at": date.today().isoformat(),
                            "version": "v3"
                        }
                    }
                )
    
    def _setup_version_specific_routes(self):
        """Set up version-specific routes using middleware."""
        # Get the route middleware
        route_middleware = None
        for middleware in self.app.middleware_manager._middleware:
            if isinstance(middleware, VersionRouteMiddleware):
                route_middleware = middleware
                break
        
        if route_middleware:
            # Register version-specific handlers
            async def v1_specific_handler(request):
                return JSONResponse(content={
                    "message": "This is a v1-specific endpoint",
                    "version": "v1",
                    "features": ["Basic functionality"]
                })
            
            async def v2_specific_handler(request):
                return JSONResponse(content={
                    "message": "This is a v2-specific endpoint",
                    "version": "v2",
                    "features": ["Enhanced functionality", "Pagination"]
                })
            
            async def v3_specific_handler(request):
                return JSONResponse(content={
                    "message": "This is a v3-specific endpoint (deprecated)",
                    "version": "v3",
                    "features": ["Experimental features", "GraphQL-like queries"],
                    "warning": "This version is deprecated and will be sunset on 2024-12-31"
                })
            
            route_middleware.register_version_route("v1", "/version-specific", v1_specific_handler)
            route_middleware.register_version_route("v2", "/version-specific", v2_specific_handler)
            route_middleware.register_version_route("v3", "/version-specific", v3_specific_handler)
    
    def _get_compatibility_matrix(self) -> Dict[str, Dict[str, bool]]:
        """Get version compatibility matrix."""
        versions = self.version_manager.get_all_versions()
        matrix = {}
        
        for v1 in versions:
            matrix[v1] = {}
            for v2 in versions:
                matrix[v1][v2] = self.version_manager.is_compatible(v1, v2)
        
        return matrix


# Create and run the application
app_instance = EnhancedVersioningApp()
app = app_instance.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8028) 