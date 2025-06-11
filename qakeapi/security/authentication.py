from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response
from pydantic import BaseModel

class AuthenticationError(Exception):
    """Base authentication error"""
    pass

class Credentials(BaseModel):
    """Base credentials model"""
    username: str
    password: str

class User(BaseModel):
    """Base user model"""
    id: str
    username: str
    is_active: bool = True
    roles: list[str] = []

class AuthenticationBackend(ABC):
    """Abstract base class for authentication backends"""
    
    @abstractmethod
    async def authenticate(self, request: Request) -> Optional[User]:
        """Authenticate a request and return a User object if successful"""
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        pass

class BasicAuthBackend(AuthenticationBackend):
    """Basic authentication backend"""
    
    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        
    async def authenticate(self, request: Request) -> Optional[User]:
        auth = request.headers.get(b"authorization")
        if not auth or not auth.startswith(b"Basic "):
            return None
            
        import base64
        try:
            decoded = base64.b64decode(auth[6:]).decode()
            username, password = decoded.split(":")
            user_data = self.users.get(username)
            
            if user_data and user_data["password"] == password:
                return User(
                    id=str(user_data["id"]),
                    username=username,
                    is_active=user_data.get("is_active", True),
                    roles=user_data.get("roles", [])
                )
        except Exception:
            return None
        
        return None
    
    async def get_user(self, user_id: str) -> Optional[User]:
        for username, user_data in self.users.items():
            if str(user_data["id"]) == user_id:
                return User(
                    id=user_id,
                    username=username,
                    is_active=user_data.get("is_active", True),
                    roles=user_data.get("roles", [])
                )
        return None
    
    def add_user(self, username: str, password: str, roles: list[str] = None):
        """Add a user to the backend"""
        import uuid
        self.users[username] = {
            "id": str(uuid.uuid4()),
            "password": password,
            "roles": roles or []
        } 