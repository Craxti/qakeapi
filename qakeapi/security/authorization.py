from abc import ABC, abstractmethod
from typing import Optional, List, Callable, Any
from qakeapi.core.requests import Request
from qakeapi.security.authentication import User

class AuthorizationError(Exception):
    """Base authorization error"""
    pass

class Permission(ABC):
    """Abstract base class for permissions"""
    
    @abstractmethod
    async def has_permission(self, request: Request, user: Optional[User]) -> bool:
        """Check if the user has this permission"""
        pass

class RolePermission(Permission):
    """Permission based on user roles"""
    
    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles
    
    async def has_permission(self, request: Request, user: Optional[User]) -> bool:
        if not user:
            return False
        return any(role in user.roles for role in self.required_roles)

class IsAuthenticated(Permission):
    """Permission that requires a user to be authenticated"""
    
    async def has_permission(self, request: Request, user: Optional[User]) -> bool:
        return user is not None and user.is_active

class IsAdmin(Permission):
    """Permission that requires a user to have admin role"""
    
    async def has_permission(self, request: Request, user: Optional[User]) -> bool:
        if not user or not user.is_active:
            return False
        return "admin" in user.roles

def requires_auth(*permissions: Permission) -> Callable:
    """Decorator to require authentication and permissions"""
    
    def decorator(handler: Callable) -> Callable:
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            user = getattr(request, "user", None)
            
            for permission in permissions:
                if not await permission.has_permission(request, user):
                    raise AuthorizationError("Permission denied")
            
            return await handler(request, *args, **kwargs)
        
        return wrapper
    
    return decorator 