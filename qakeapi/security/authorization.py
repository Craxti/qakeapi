from abc import ABC, abstractmethod
from functools import wraps
import logging
from typing import Any, Callable, List, Optional

from qakeapi.core.responses import Response
from qakeapi.core.interfaces import UserProtocol
from qakeapi.core.requests import Request

logger = logging.getLogger(__name__)


class AuthorizationError(Exception):
    """Base authorization error"""

    pass


class Permission(ABC):
    """Abstract base class for permissions"""

    @abstractmethod
    async def has_permission(self, user: Optional[UserProtocol]) -> bool:
        """Check if user has this permission"""
        pass


class IsAuthenticated(Permission):
    """Permission that requires user to be authenticated"""

    async def has_permission(self, user: Optional[UserProtocol]) -> bool:
        logger.debug(f"Checking IsAuthenticated permission for user: {user}")
        has_permission = user is not None
        logger.debug(f"IsAuthenticated permission result: {has_permission}")
        return has_permission


class IsAdmin(Permission):
    """Permission that requires user to have admin role"""

    async def has_permission(self, user: Optional[UserProtocol]) -> bool:
        logger.debug(f"Checking IsAdmin permission for user: {user}")
        if not user:
            return False
        has_permission = "admin" in user.roles
        logger.debug(f"IsAdmin permission result: {has_permission}")
        return has_permission


class RolePermission(Permission):
    """Permission that requires user to have specific role"""

    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles

    async def has_permission(self, user: Optional[UserProtocol]) -> bool:
        logger.debug(f"Checking RolePermission {self.required_roles} for user: {user}")
        if not user:
            return False
        has_permission = any(role in user.roles for role in self.required_roles)
        logger.debug(f"RolePermission result: {has_permission}")
        return has_permission


def requires_auth(permission: Permission) -> Callable:
    """Decorator to protect routes with permissions"""

    def decorator(handler: Callable) -> Callable:
        @wraps(handler)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Response:
            try:
                logger.debug(f"Checking permission {permission.__class__.__name__} for request: {request}")
                user = getattr(request, "user", None)
                logger.debug(f"User from request: {user}")

                has_permission = await permission.has_permission(user)
                logger.debug(f"Permission check result: {has_permission}")

                if not has_permission:
                    logger.debug("Permission denied")
                    return Response.json({"detail": "Unauthorized"}, status_code=401)

                logger.debug("Permission granted")
                try:
                    response = await handler(request, *args, **kwargs)
                    logger.debug(f"Handler response: {response}")
                    if isinstance(response, Response):
                        return response
                    return Response.json(response)
                except Exception as e:
                    logger.error(f"Error in handler: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    return Response.json({"detail": "Internal server error"}, status_code=500)

            except Exception as e:
                logger.error(f"Error checking permissions: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return Response.json({"detail": "Internal server error"}, status_code=500)

        return wrapper

    return decorator
