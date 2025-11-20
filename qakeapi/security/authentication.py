from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional
import traceback
from datetime import datetime, timedelta

import jwt
from pydantic import BaseModel

from qakeapi.core.responses import Response
from qakeapi.core.interfaces import UserProtocol

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Base authentication error"""

    pass


class Credentials(BaseModel):
    """Base credentials model"""

    username: str
    password: str


class User(UserProtocol):
    def __init__(self, username: str, roles: List[str], metadata: Dict[str, Any] = None):
        self._username = username
        self._roles = roles
        self._metadata = metadata or {}

    @property
    def username(self) -> str:
        return self._username

    @property
    def roles(self) -> List[str]:
        return self._roles

    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        return self._metadata


class AuthenticationBackend(ABC):
    """Abstract base class for authentication backends"""

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, str]) -> Optional[UserProtocol]:
        """Authenticate user with given credentials"""
        pass

    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[UserProtocol]:
        """Get user by ID"""
        pass


class BasicAuthBackend(AuthenticationBackend):
    """Basic authentication backend"""

    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        logger.debug("Initialized BasicAuthBackend")

    def add_user(self, username: str, password: str, roles: List[str] = None):
        """Add a user to the backend"""
        self.users[username] = {
            "password": password,
            "roles": roles or [],
            "metadata": {},
        }
        logger.debug(f"Added user: {username} with roles: {roles}")
        logger.debug(f"Current users: {self.users}")

    async def authenticate(self, credentials: Dict[str, str]) -> Optional[UserProtocol]:
        """Authenticate user with basic auth credentials"""
        try:
            logger.debug(f"Authenticating with credentials: {credentials}")
            logger.debug(f"Available users: {self.users}")
            
            username = credentials.get("username")
            password = credentials.get("password")

            logger.debug(f"Attempting to authenticate user: {username}")

            if not username or not password:
                logger.debug("Missing username or password")
                return None

            user_data = self.users.get(username)
            if not user_data:
                logger.debug(f"User not found: {username}")
                return None
                
            logger.debug(f"Found user data: {user_data}")
            logger.debug(f"Comparing passwords: {password} == {user_data['password']}")

            if user_data["password"] != password:
                logger.debug(f"Invalid password for user: {username}")
                return None

            return User(
                username=username,
                roles=user_data["roles"],
                metadata=user_data.get("metadata")
            )
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return None

    async def get_user(self, user_id: str) -> Optional[UserProtocol]:
        """Get user by username"""
        try:
            logger.debug(f"Getting user by ID: {user_id}")
            user_data = self.users.get(user_id)
            if not user_data:
                logger.debug(f"User not found: {user_id}")
                return None

            user = User(
                username=user_id, 
                roles=user_data["roles"], 
                metadata=user_data.get("metadata", {})
            )
            logger.debug(f"Found user: {user}")
            return user
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            logger.error(traceback.format_exc())
            raise AuthenticationError("Failed to get user")


@dataclass
class JWTConfig:
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


class JWTAuthBackend(AuthenticationBackend):
    """JWT authentication backend"""

    def __init__(self, config: JWTConfig):
        self.config = config
        self.users: Dict[str, Dict[str, Any]] = {}
        logger.debug("Initialized JWTAuthBackend")

    def add_user(self, username: str, password: str, roles: List[str] = None):
        """Add a user to the backend"""
        self.users[username] = {
            "password": password,
            "roles": roles or [],
            "metadata": {},
        }
        logger.debug(f"Added user: {username} with roles: {roles}")

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        try:
            encoded_jwt = jwt.encode(data, self.config.secret_key, algorithm=self.config.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise AuthenticationError("Failed to create access token")

    async def authenticate(self, credentials: Dict[str, str]) -> Optional[UserProtocol]:
        """Authenticate user with JWT credentials"""
        try:
            username = credentials.get("username")
            password = credentials.get("password")

            if not username or not password:
                return None

            user_data = self.users.get(username)
            if not user_data or user_data["password"] != password:
                return None

            return User(
                username=username,
                roles=user_data["roles"],
                metadata=user_data.get("metadata")
            )
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return None

    async def get_current_user(self, token: str) -> Optional[UserProtocol]:
        """Get current user from JWT token"""
        try:
            payload = jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
            username = payload.get("sub")
            if not username:
                return None
            return await self.get_user(username)
        except jwt.PyJWTError as e:
            logger.error(f"JWT error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None

    async def get_user(self, user_id: str) -> Optional[UserProtocol]:
        """Get user by username"""
        try:
            user_data = self.users.get(user_id)
            if not user_data:
                return None

            return User(
                username=user_id,
                roles=user_data["roles"],
                metadata=user_data.get("metadata", {})
            )
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            raise AuthenticationError("Failed to get user")
