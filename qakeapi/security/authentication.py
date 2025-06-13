from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from qakeapi.core.requests import Request
from qakeapi.core.responses import Response


class AuthenticationError(Exception):
    """Base authentication error"""

    pass


class Credentials(BaseModel):
    """Base credentials model"""

    username: str
    password: str


@dataclass
class User:
    username: str
    roles: List[str]
    metadata: Dict[str, Any] = None


class AuthenticationBackend(ABC):
    """Abstract base class for authentication backends"""

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, str]) -> Optional[User]:
        """Authenticate user with given credentials"""
        pass

    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        pass


class BasicAuthBackend(AuthenticationBackend):
    """Basic authentication backend"""

    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}

    def add_user(self, username: str, password: str, roles: List[str] = None):
        """Add a user to the backend"""
        self.users[username] = {
            "password": password,
            "roles": roles or [],
            "metadata": {},
        }

    async def authenticate(self, credentials: Dict[str, str]) -> Optional[User]:
        """Authenticate user with basic auth credentials"""
        username = credentials.get("username")
        password = credentials.get("password")

        if not username or not password:
            return None

        user_data = self.users.get(username)
        if not user_data or user_data["password"] != password:
            return None

        return User(
            username=username, roles=user_data["roles"], metadata=user_data["metadata"]
        )

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by username"""
        user_data = self.users.get(user_id)
        if not user_data:
            return None

        return User(
            username=user_id, roles=user_data["roles"], metadata=user_data["metadata"]
        )
