from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt

from .authentication import AuthenticationBackend, AuthenticationError, User


class JWTConfig:
    """Configuration for JWT authentication"""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        token_type: str = "Bearer",
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.token_type = token_type


class JWTAuthBackend(AuthenticationBackend):
    """JWT authentication backend implementation"""

    def __init__(self, config: JWTConfig):
        self.config = config
        self.users: Dict[str, Dict[str, Any]] = {}

    def add_user(self, username: str, password: str, roles: list[str] = None):
        """Add a user to the backend"""
        self.users[username] = {
            "password": password,
            "roles": roles or [],
            "metadata": {},
        }

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.config.access_token_expire_minutes
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, self.config.secret_key, algorithm=self.config.algorithm
        )
        return encoded_jwt

    async def authenticate(self, credentials: Dict[str, str]) -> Optional[User]:
        """Authenticate user with JWT token or username/password"""
        if "token" in credentials:
            try:
                payload = jwt.decode(
                    credentials["token"],
                    self.config.secret_key,
                    algorithms=[self.config.algorithm],
                )
                username = payload.get("sub")
                if username is None:
                    return None

                user_data = self.users.get(username)
                if not user_data:
                    return None

                return User(
                    username=username,
                    roles=user_data["roles"],
                    metadata=user_data["metadata"],
                )
            except jwt.PyJWTError:
                raise AuthenticationError("Invalid token")

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
