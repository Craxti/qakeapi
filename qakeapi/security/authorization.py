from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Any
from functools import wraps
from .authentication import User
from qakeapi.core.responses import Response

class AuthorizationError(Exception):
    """Base authorization error"""
    pass

class Permission(ABC):
    """Abstract base class for permissions"""
    
    @abstractmethod
    async def has_permission(self, user: Optional[User]) -> bool:
        """Check if user has this permission"""
        pass

class IsAuthenticated(Permission):
    """Permission that requires user to be authenticated"""
    
    async def has_permission(self, user: Optional[User]) -> bool:
        return user is not None

class IsAdmin(Permission):
    """Permission that requires user to have admin role"""
    
    async def has_permission(self, user: Optional[User]) -> bool:
        if not user:
            return False
        return "admin" in user.roles

class RolePermission(Permission):
    """Permission that requires user to have specific role"""
    
    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles
    
    async def has_permission(self, user: Optional[User]) -> bool:
        if not user:
            return False
        return any(role in user.roles for role in self.required_roles)

def requires_auth(permission: Permission) -> Callable:
    """Decorator to protect routes with permissions"""
    
    def decorator(handler: Callable) -> Callable:
        @wraps(handler)
        async def wrapper(request, *args: Any, **kwargs: Any) -> Response:
            user = getattr(request, "user", None)
            
            if not await permission.has_permission(user):
                return Response.json(
                    {"detail": "Unauthorized"},
                    status_code=401
                )
            
            return await handler(request, *args, **kwargs)
        return wrapper
    return decorator 