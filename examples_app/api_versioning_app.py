# -*- coding: utf-8 -*-
"""
API Versioning example with QakeAPI.
"""
import sys
import os
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.validation.models import validate_request_body, RequestModel
from qakeapi.api.versioning import VersionInfo, PathVersionStrategy, HeaderVersionStrategy, APIVersionManager, VersionStatus
from qakeapi.api.deprecation import DeprecationWarning, DeprecationLevel
from pydantic import BaseModel, Field

# Initialize application with API versioning
app = Application(
    title="API Versioning Example",
    version="1.0.3",
    description="Demonstrates API versioning capabilities"
)

# Configure versioning strategy
path_strategy = PathVersionStrategy(["v1", "v2", "v3"], "v1")
app.version_manager = APIVersionManager(path_strategy)

# Add version information
app.version_manager.register_version(VersionInfo(
    version="v1",
    status=VersionStatus.ACTIVE,
    release_date=date(2024, 1, 1),
    description="Basic user management",
    new_features=["Basic user management", "Simple authentication"],
    bug_fixes=[]
))

app.version_manager.register_version(VersionInfo(
    version="v2", 
    status=VersionStatus.ACTIVE,
    release_date=date(2024, 6, 1),
    description="Enhanced user management",
    breaking_changes=["User ID format changed", "Response structure updated"],
    new_features=["Advanced user management", "Role-based access control"],
    bug_fixes=["Fixed authentication bug", "Improved error handling"]
))

app.version_manager.register_version(VersionInfo(
    version="v3",
    status=VersionStatus.ACTIVE,
    release_date=date(2024, 12, 1),
    description="Advanced API with GraphQL support",
    breaking_changes=["API response format changed", "New authentication required"],
    new_features=["GraphQL support", "Real-time notifications"],
    bug_fixes=["Performance improvements", "Security enhancements"]
))

# Add deprecation warnings
app.deprecation_manager.add_deprecation("old_user_endpoint", DeprecationWarning(
    feature="old_user_endpoint",
    version="v1",
    deprecation_date=datetime(2024, 6, 1),
    sunset_date=datetime(2025, 6, 1),
    replacement="new_user_endpoint",
    migration_guide="https://docs.example.com/migration/v1-to-v2"
))

app.deprecation_manager.add_deprecation("basic_auth", DeprecationWarning(
    feature="basic_auth",
    version="v2",
    deprecation_date=datetime(2024, 12, 1),
    sunset_date=datetime(2025, 12, 1),
    replacement="jwt_auth",
    migration_guide="https://docs.example.com/migration/v2-to-v3"
))

# Pydantic models for different versions
class UserV1(BaseModel):
    id: int
    name: str
    email: str

class UserV2(BaseModel):
    user_id: str  # Changed from id to user_id
    name: str
    email: str
    role: str = "user"  # New field
    created_at: datetime

class UserV3(BaseModel):
    user_id: str
    name: str
    email: str
    role: str = "user"
    created_at: datetime
    updated_at: datetime
    status: str = "active"  # New field
    metadata: Dict[str, Any] = {}  # New field

# Database simulation
users_db_v1 = {
    1: {"id": 1, "name": "John Doe", "email": "john@example.com"},
    2: {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
}

users_db_v2 = {
    "user_001": {"user_id": "user_001", "name": "John Doe", "email": "john@example.com", "role": "user", "created_at": datetime(2024, 1, 1).isoformat()},
    "user_002": {"user_id": "user_002", "name": "Jane Smith", "email": "jane@example.com", "role": "admin", "created_at": datetime(2024, 1, 2).isoformat()}
}

users_db_v3 = {
    "user_001": {
        "user_id": "user_001", 
        "name": "John Doe", 
        "email": "john@example.com", 
        "role": "user", 
        "created_at": datetime(2024, 1, 1).isoformat(),
        "updated_at": datetime(2024, 12, 1).isoformat(),
        "status": "active",
        "metadata": {"preferences": {"theme": "dark"}}
    }
}

# Version-specific routes

@app.get("/v1/users")
async def get_users_v1(request: Request):
    """Get users (v1 format)."""
    return {
        "users": list(users_db_v1.values()),
        "version": "v1",
        "total": len(users_db_v1)
    }

@app.get("/v1/users/{user_id}")
async def get_user_v1(request: Request):
    """Get user by ID (v1 format)."""
    user_id = int(request.path_params.get("user_id"))
    if user_id in users_db_v1:
        return users_db_v1[user_id]
    return Response.json({"error": "User not found"}, status_code=404)

@app.get("/v2/users")
async def get_users_v2(request: Request):
    """Get users (v2 format)."""
    return {
        "data": {
            "users": list(users_db_v2.values()),
            "pagination": {
                "total": len(users_db_v2),
                "page": 1,
                "per_page": 10
            }
        },
        "version": "v2"
    }

@app.get("/v2/users/{user_id}")
async def get_user_v2(request: Request):
    """Get user by ID (v2 format)."""
    user_id = request.path_params.get("user_id")
    if user_id in users_db_v2:
        return {"data": users_db_v2[user_id], "version": "v2"}
    return Response.json({"error": "User not found"}, status_code=404)

@app.get("/v3/users")
async def get_users_v3(request: Request):
    """Get users (v3 format)."""
    return {
        "success": True,
        "data": {
            "users": list(users_db_v3.values()),
            "pagination": {
                "total": len(users_db_v3),
                "page": 1,
                "per_page": 10,
                "has_next": False
            }
        },
        "meta": {
            "version": "v3",
            "timestamp": datetime.now().isoformat()
        }
    }

@app.get("/v3/users/{user_id}")
async def get_user_v3(request: Request):
    """Get user by ID (v3 format)."""
    user_id = request.path_params.get("user_id")
    if user_id in users_db_v3:
        return {
            "success": True,
            "data": users_db_v3[user_id],
            "meta": {
                "version": "v3",
                "timestamp": datetime.now().isoformat()
            }
        }
    return Response.json({"success": False, "error": "User not found"}, status_code=404)

# Deprecated endpoint example
@app.get("/v1/old-users")
async def get_old_users(request: Request):
    """Deprecated endpoint - will show deprecation warning."""
    # Check deprecation
    warning = app.deprecation_manager.check_deprecation("old_user_endpoint", request)
    
    return {
        "users": list(users_db_v1.values()),
        "deprecation_warning": warning,
        "message": "This endpoint is deprecated. Use /v1/users instead."
    }

# API information endpoints
@app.get("/api/versions")
async def get_versions(request: Request):
    """Get version information."""
    try:
        versions_info = {}
        for version in app.version_manager.get_all_versions():
            info = app.version_manager.get_version_info(version)
            if info:
                versions_info[version] = {
                    "status": info.status.value,
                    "release_date": info.release_date.isoformat() if info.release_date else None,
                    "description": info.description,
                    "new_features": info.new_features,
                    "breaking_changes": info.breaking_changes,
                    "bug_fixes": info.bug_fixes
                }
        
        return {
            "versions": versions_info,
            "total": len(versions_info),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return Response.json({"error": str(e)}, status_code=500)

@app.get("/api/changelog")
async def get_changelog(request: Request):
    """Get API changelog."""
    try:
        changelog = []
        for version in app.version_manager.get_all_versions():
            info = app.version_manager.get_version_info(version)
            if info:
                changelog.append({
                    "version": version,
                    "release_date": info.release_date.isoformat() if info.release_date else None,
                    "description": info.description,
                    "new_features": info.new_features,
                    "breaking_changes": info.breaking_changes,
                    "bug_fixes": info.bug_fixes
                })
        
        # Sort by release date (newest first)
        changelog.sort(key=lambda x: x["release_date"] or "", reverse=True)
        
        return {
            "changelog": changelog,
            "total": len(changelog),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return Response.json({"error": str(e)}, status_code=500)

@app.get("/api/deprecations")
async def get_deprecations(request: Request):
    """Get deprecation information."""
    try:
        # Get deprecation information from the manager
        deprecations = []
        for feature, deprecation in app.deprecation_manager.deprecations.items():
            deprecations.append({
                "feature": feature,
                "version": deprecation.version,
                "deprecation_date": deprecation.deprecation_date.isoformat() if deprecation.deprecation_date else None,
                "sunset_date": deprecation.sunset_date.isoformat() if deprecation.sunset_date else None,
                "replacement": deprecation.replacement,
                "migration_guide": deprecation.migration_guide
            })
        
        return {
            "deprecations": deprecations,
            "total": len(deprecations),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return Response.json({"error": str(e)}, status_code=500)

@app.get("/")
async def root(request: Request):
    """Root endpoint with version information."""
    return {
        "message": "API Versioning Example",
        "current_version": app.version,
        "supported_versions": app.version_manager.get_all_versions(),
        "endpoints": {
            "v1": "/v1/users - User management (v1)",
            "v2": "/v2/users - User management (v2)", 
            "v3": "/v3/users - User management (v3)",
            "deprecated": "/v1/old-users - Deprecated endpoint",
            "versions": "/api/versions - Version information",
            "changelog": "/api/changelog - API changelog",
            "deprecations": "/api/deprecations - Deprecation information"
        }
    }

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": app.version,
        "timestamp": datetime.now().isoformat(),
        "supported_versions": app.version_manager.get_all_versions()
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting API Versioning Example...")
    print("📖 Available endpoints:")
    print("  - /v1/users - User management (v1)")
    print("  - /v2/users - User management (v2)")
    print("  - /v3/users - User management (v3)")
    print("  - /api/versions - Version information")
    print("  - /api/changelog - API changelog")
    print("  - /api/deprecations - Deprecation information")
    print("  - /docs - API documentation")
    print()
    uvicorn.run(app, host="127.0.0.1", port=8020) 