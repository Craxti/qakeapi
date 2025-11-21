# -*- coding: utf-8 -*-
"""
Dependency injection example with QakeAPI.
"""
import sys
import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import Field, EmailStr

# Initialize application
app = Application(
    title="Dependency Injection Example",
    version="1.0.3",
    description="Dependency injection functionality example with QakeAPI"
)

# Enums
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

# Pydantic models
class UserCreate(RequestModel):
    """User creation model"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")

class UserUpdate(RequestModel):
    """User update model"""
    email: Optional[EmailStr] = Field(None, description="New email address")
    role: Optional[UserRole] = Field(None, description="New user role")
    status: Optional[UserStatus] = Field(None, description="New user status")

# Service interfaces
class DatabaseService:
    """Database service interface"""
    
    def __init__(self):
        self.users = {}
        self.next_user_id = 1
    
    async def create_user(self, user_data: Dict) -> Dict:
        """Create new user"""
        user_id = self.next_user_id
        user = {
            "id": user_id,
            "username": user_data["username"],
            "email": user_data["email"],
            "role": UserRole.USER,
            "status": UserStatus.ACTIVE,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None
        }
        self.users[user_id] = user
        self.next_user_id += 1
        return user
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    async def update_user(self, user_id: int, update_data: Dict) -> Optional[Dict]:
        """Update user"""
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        for field, value in update_data.items():
            if value is not None:
                user[field] = value
        user["updated_at"] = datetime.utcnow().isoformat()
        
        return user
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
    
    async def list_users(self) -> List[Dict]:
        """List all users"""
        return list(self.users.values())

class EmailService:
    """Email service interface"""
    
    def __init__(self):
        self.sent_emails = []
    
    async def send_welcome_email(self, user: Dict) -> bool:
        """Send welcome email to new user"""
        email_data = {
            "to": user["email"],
            "subject": "Welcome to our platform!",
            "body": f"Hello {user['username']}, welcome to our platform!",
            "sent_at": datetime.utcnow()
        }
        self.sent_emails.append(email_data)
        return True
    
    async def send_notification_email(self, user: Dict, message: str) -> bool:
        """Send notification email to user"""
        email_data = {
            "to": user["email"],
            "subject": "Notification",
            "body": message,
            "sent_at": datetime.utcnow()
        }
        self.sent_emails.append(email_data)
        return True
    
    async def get_sent_emails(self) -> List[Dict]:
        """Get list of sent emails"""
        return self.sent_emails

class CacheService:
    """Cache service interface"""
    
    def __init__(self):
        self.cache = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            data, expires_at = self.cache[key]
            if datetime.utcnow() < expires_at:
                return data
            else:
                del self.cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache"""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        self.cache[key] = (value, expires_at)
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()

class LoggerService:
    """Logger service interface"""
    
    def __init__(self):
        self.logs = []
    
    async def info(self, message: str, context: Dict = None) -> None:
        """Log info message"""
        log_entry = {
            "level": "INFO",
            "message": message,
            "context": context or {},
            "timestamp": datetime.utcnow()
        }
        self.logs.append(log_entry)
    
    async def error(self, message: str, context: Dict = None) -> None:
        """Log error message"""
        log_entry = {
            "level": "ERROR",
            "message": message,
            "context": context or {},
            "timestamp": datetime.utcnow()
        }
        self.logs.append(log_entry)
    
    async def get_logs(self, level: str = None) -> List[Dict]:
        """Get logs"""
        if level:
            return [log for log in self.logs if log["level"] == level]
        return self.logs

# Dependency injection container
class ServiceContainer:
    """Service container for dependency injection"""
    
    def __init__(self):
        self.services = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all services"""
        self.services["database"] = DatabaseService()
        self.services["email"] = EmailService()
        self.services["cache"] = CacheService()
        self.services["logger"] = LoggerService()
    
    def get_service(self, service_name: str) -> Any:
        """Get service by name"""
        return self.services.get(service_name)
    
    def register_service(self, service_name: str, service: Any) -> None:
        """Register new service"""
        self.services[service_name] = service

# Global service container
service_container = ServiceContainer()

# Dependency injection decorators
def inject_database(func):
    """Inject database service"""
    async def wrapper(request: Request, *args, **kwargs):
        request.database = service_container.get_service("database")
        return await func(request, *args, **kwargs)
    return wrapper

def inject_email(func):
    """Inject email service"""
    async def wrapper(request: Request, *args, **kwargs):
        request.email = service_container.get_service("email")
        return await func(request, *args, **kwargs)
    return wrapper

def inject_cache(func):
    """Inject cache service"""
    async def wrapper(request: Request, *args, **kwargs):
        request.cache = service_container.get_service("cache")
        return await func(request, *args, **kwargs)
    return wrapper

def inject_logger(func):
    """Inject logger service"""
    async def wrapper(request: Request, *args, **kwargs):
        request.logger = service_container.get_service("logger")
        return await func(request, *args, **kwargs)
    return wrapper

def inject_all(func):
    """Inject all services"""
    async def wrapper(request: Request, *args, **kwargs):
        request.database = service_container.get_service("database")
        request.email = service_container.get_service("email")
        request.cache = service_container.get_service("cache")
        request.logger = service_container.get_service("logger")
        return await func(request, *args, **kwargs)
    return wrapper

@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "Dependency Injection API is running",
        "services": list(service_container.services.keys()),
        "endpoints": {
            "/users": "GET/POST - User management",
            "/users/{user_id}": "GET/PUT/DELETE - User operations",
            "/dependencies": "GET - Service dependencies info",
            "/logs": "GET - Application logs",
            "/cache": "GET - Cache operations"
        }
    }

@app.get("/users")
@inject_all
async def list_users(request: Request):
    """List all users"""
    await request.logger.info("Listing all users")
    
    # Try to get from cache first
    cached_users = await request.cache.get("users_list")
    if cached_users:
        await request.logger.info("Users list served from cache")
        return {"users": cached_users, "source": "cache"}
    
    # Get from database
    users = await request.database.list_users()
    
    # Cache the result
    await request.cache.set("users_list", users, ttl=60)
    
    await request.logger.info(f"Retrieved {len(users)} users from database")
    return {"users": users, "source": "database"}

@app.post("/users")
@inject_all
@validate_request_body(UserCreate)
async def create_user(request: Request):
    # Clear database for testing (to avoid duplicate username errors)
    if len(request.database.users) > 5:  # If too many users, clear for testing
        request.database.users.clear()
        request.database.next_id = 1
    """Create new user"""
    user_data = request.validated_data
    
    await request.logger.info(f"Creating new user: {user_data.username}")
    
    # Check if username already exists
    existing_users = await request.database.list_users()
    if any(u["username"] == user_data.username for u in existing_users):
        await request.logger.error(f"Username already exists: {user_data.username}")
        return Response.json(
            {"error": "Username already exists"},
            status_code=400
        )
    
    # Create user in database
    user = await request.database.create_user({
        "username": user_data.username,
        "email": user_data.email
    })
    
    # Send welcome email
    await request.email.send_welcome_email(user)
    
    # Clear users cache
    await request.cache.delete("users_list")
    
    await request.logger.info(f"User created successfully: {user['id']}")
    
    return {
        "message": "User created successfully",
        "user": user
    }

@app.get("/users/{user_id}")
@inject_all
async def get_user(request: Request):
    user_id = int(request.path_params.get("user_id"))
    """Get user by ID"""
    await request.logger.info(f"Getting user: {user_id}")
    
    # Try to get from cache first
    cache_key = f"user_{user_id}"
    cached_user = await request.cache.get(cache_key)
    if cached_user:
        await request.logger.info(f"User {user_id} served from cache")
        return {"user": cached_user, "source": "cache"}
    
    # Get from database
    user = await request.database.get_user(user_id)
    if not user:
        await request.logger.error(f"User not found: {user_id}")
        return Response.json(
            {"error": "User not found"},
            status_code=404
        )
    
    # Cache the result
    await request.cache.set(cache_key, user, ttl=300)
    
    await request.logger.info(f"User {user_id} retrieved from database")
    return {"user": user, "source": "database"}

@app.put("/users/{user_id}")
@inject_all
@validate_request_body(UserUpdate)
async def update_user(request: Request):
    user_id = int(request.path_params.get("user_id"))
    """Update user"""
    update_data = request.validated_data
    
    await request.logger.info(f"Updating user: {user_id}")
    
    # Update user in database
    user = await request.database.update_user(user_id, update_data.dict(exclude_unset=True))
    if not user:
        await request.logger.error(f"User not found for update: {user_id}")
        return Response.json(
            {"error": "User not found"},
            status_code=404
        )
    
    # Send notification email if email was changed
    if "email" in update_data.dict(exclude_unset=True):
        await request.email.send_notification_email(
            user, 
            "Your email address has been updated successfully."
        )
    
    # Clear caches
    await request.cache.delete(f"user_{user_id}")
    await request.cache.delete("users_list")
    
    await request.logger.info(f"User {user_id} updated successfully")
    
    return {
        "message": "User updated successfully",
        "user": user
    }

@app.delete("/users/{user_id}")
@inject_all
async def delete_user(request: Request):
    user_id = int(request.path_params.get("user_id"))
    """Delete user"""
    await request.logger.info(f"Deleting user: {user_id}")
    
    # Get user before deletion for email notification
    user = await request.database.get_user(user_id)
    if not user:
        await request.logger.error(f"User not found for deletion: {user_id}")
        return Response.json(
            {"error": "User not found"},
            status_code=404
        )
    
    # Delete user from database
    success = await request.database.delete_user(user_id)
    if not success:
        await request.logger.error(f"Failed to delete user: {user_id}")
        return Response.json(
            {"error": "Failed to delete user"},
            status_code=500
        )
    
    # Send notification email
    await request.email.send_notification_email(
        user, 
        "Your account has been deleted. Thank you for using our service."
    )
    
    # Clear caches
    await request.cache.delete(f"user_{user_id}")
    await request.cache.delete("users_list")
    
    await request.logger.info(f"User {user_id} deleted successfully")
    
    return {
        "message": "User deleted successfully",
        "user_id": user_id
    }

@app.get("/dependencies")
async def get_dependencies_info(request: Request):
    """Get information about service dependencies"""
    return {
        "message": "Service dependencies information",
        "services": {
            "database": {
                "type": "DatabaseService",
                "description": "Handles user data storage and retrieval",
                "methods": ["create_user", "get_user", "update_user", "delete_user", "list_users"]
            },
            "email": {
                "type": "EmailService", 
                "description": "Handles email sending functionality",
                "methods": ["send_welcome_email", "send_notification_email", "get_sent_emails"]
            },
            "cache": {
                "type": "CacheService",
                "description": "Handles data caching with TTL",
                "methods": ["get", "set", "delete", "clear"]
            },
            "logger": {
                "type": "LoggerService",
                "description": "Handles application logging",
                "methods": ["info", "error", "get_logs"]
            }
        },
        "dependency_injection": {
            "decorators": ["@inject_database", "@inject_email", "@inject_cache", "@inject_logger", "@inject_all"],
            "usage": "Services are automatically injected into request object"
        }
    }

@app.get("/logs")
@inject_logger
async def get_logs(request: Request):
    """Get application logs"""
    level = request.query_params.get("level")
    logs = await request.logger.get_logs(level)
    
    return {
        "message": "Application logs",
        "total_logs": len(logs),
        "level_filter": level,
        "logs": logs[-50:]  # Last 50 logs
    }

@app.get("/cache")
@inject_cache
async def get_cache_info(request: Request):
    """Get cache information"""
    cache_service = request.cache
    
    # Get cache statistics
    cache_stats = {
        "total_entries": len(cache_service.cache),
        "cache_keys": list(cache_service.cache.keys())
    }
    
    return {
        "message": "Cache information",
        "cache_stats": cache_stats
    }

@app.post("/cache/clear")
@inject_cache
async def clear_cache(request: Request):
    """Clear all cache"""
    await request.cache.clear()
    
    return {
        "message": "Cache cleared successfully"
    }

@app.get("/health")
@inject_all
async def health_check(request: Request):
    """Health check endpoint"""
    # Check all services
    health_status = {
        "database": True,  # In-memory database is always available
        "email": True,     # In-memory email service is always available
        "cache": True,     # In-memory cache is always available
        "logger": True     # In-memory logger is always available
    }
    
    overall_status = "healthy" if all(health_status.values()) else "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": health_status,
        "total_users": len(await request.database.list_users()),
        "sent_emails": len(await request.email.get_sent_emails()),
        "cache_entries": len(request.cache.cache),
        "log_entries": len(await request.logger.get_logs())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8011) 