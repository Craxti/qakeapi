"""
WebSocket Authentication System following SOLID principles.

This module provides a flexible and extensible authentication system for WebSocket connections.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional, Union, Callable, Awaitable
from dataclasses import field
import jwt
import hashlib
import secrets

from qakeapi.core.websockets import WebSocketConnection

logger = logging.getLogger(__name__)

class AuthStatus(Enum):
    """Authentication status enumeration."""
    PENDING = "pending"
    AUTHENTICATED = "authenticated"
    UNAUTHENTICATED = "unauthenticated"
    EXPIRED = "expired"
    INVALID = "invalid"

@dataclass
class AuthResult:
    """Result of authentication attempt."""
    status: AuthStatus
    user_id: Optional[str] = None
    user_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AuthConfig:
    """Configuration for authentication."""
    secret_key: str
    algorithm: str = "HS256"
    token_expiry: timedelta = field(default_factory=lambda: timedelta(hours=1))
    max_auth_attempts: int = 3
    auth_timeout: float = 30.0  # seconds
    require_auth: bool = True
    allow_anonymous: bool = False

class WebSocketAuthenticator(ABC):
    """
    Abstract base class for WebSocket authentication.
    
    Following SOLID principles:
    - Single Responsibility: Only handles authentication
    - Open/Closed: Extensible through inheritance
    - Liskov Substitution: Can be replaced with any implementation
    - Interface Segregation: Focused interface
    - Dependency Inversion: Depends on abstractions
    """
    
    @abstractmethod
    async def authenticate(self, websocket: WebSocketConnection, auth_data: Dict[str, Any]) -> AuthResult:
        """Authenticate a WebSocket connection."""
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> AuthResult:
        """Validate an authentication token."""
        pass
    
    @abstractmethod
    async def create_token(self, user_data: Dict[str, Any]) -> str:
        """Create an authentication token."""
        pass
    
    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """Revoke an authentication token."""
        pass

class JWTAuthenticator(WebSocketAuthenticator):
    """
    JWT-based WebSocket authenticator.
    
    Implements JWT token authentication for WebSocket connections.
    """
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self._revoked_tokens: set = set()
        self._auth_attempts: Dict[str, int] = {}
    
    async def authenticate(self, websocket: WebSocketConnection, auth_data: Dict[str, Any]) -> AuthResult:
        """Authenticate using JWT token."""
        try:
            token = auth_data.get("token")
            if not token:
                return AuthResult(
                    status=AuthStatus.UNAUTHENTICATED,
                    error_message="No token provided"
                )
            
            # Check if token is revoked
            if token in self._revoked_tokens:
                return AuthResult(
                    status=AuthStatus.INVALID,
                    error_message="Token has been revoked"
                )
            
            # Validate token
            result = await self.validate_token(token)
            if result.status == AuthStatus.AUTHENTICATED:
                # Reset auth attempts on successful authentication
                self._auth_attempts[websocket.connection_id] = 0
                
            return result
            
        except Exception as e:
            logger.error(f"Authentication error for {websocket.connection_id}: {e}")
            return AuthResult(
                status=AuthStatus.INVALID,
                error_message=f"Authentication failed: {str(e)}"
            )
    
    async def validate_token(self, token: str) -> AuthResult:
        """Validate JWT token."""
        try:
            # Check if token is revoked first
            if token in self._revoked_tokens:
                return AuthResult(
                    status=AuthStatus.INVALID,
                    error_message="Token has been revoked"
                )
            
            payload = jwt.decode(
                token, 
                self.config.secret_key, 
                algorithms=[self.config.algorithm]
            )
            
            # Check expiration
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                exp_time = datetime.fromtimestamp(exp_timestamp)
                if datetime.now() > exp_time:
                    return AuthResult(
                        status=AuthStatus.EXPIRED,
                        error_message="Token has expired"
                    )
            
            return AuthResult(
                status=AuthStatus.AUTHENTICATED,
                user_id=payload.get("user_id"),
                user_data=payload.get("user_data", {}),
                expires_at=exp_time if exp_timestamp else None,
                metadata=payload.get("metadata", {})
            )
            
        except jwt.ExpiredSignatureError:
            return AuthResult(
                status=AuthStatus.EXPIRED,
                error_message="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            return AuthResult(
                status=AuthStatus.INVALID,
                error_message=f"Invalid token: {str(e)}"
            )
    
    async def create_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT token."""
        payload = {
            "user_id": user_data.get("user_id"),
            "user_data": user_data,
            "exp": datetime.utcnow() + self.config.token_expiry,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(32)  # JWT ID for uniqueness
        }
        
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
    
    async def revoke_token(self, token: str) -> bool:
        """Revoke JWT token."""
        try:
            # Decode to validate token structure
            jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
            self._revoked_tokens.add(token)
            return True
        except jwt.InvalidTokenError:
            return False

class WebSocketAuthMiddleware:
    """
    Middleware for WebSocket authentication.
    
    Handles authentication flow and connection management.
    """
    
    def __init__(self, authenticator: WebSocketAuthenticator, config: AuthConfig):
        self.authenticator = authenticator
        self.config = config
        self._authenticated_connections: Dict[str, AuthResult] = {}
        self._auth_attempts: Dict[str, int] = {}
    
    async def authenticate_connection(self, websocket: WebSocketConnection) -> AuthResult:
        """Authenticate a WebSocket connection."""
        connection_id = websocket.connection_id
        
        # Check if already authenticated
        if connection_id in self._authenticated_connections:
            return self._authenticated_connections[connection_id]
        
        # Check auth attempts
        attempts = self._auth_attempts.get(connection_id, 0)
        if attempts >= self.config.max_auth_attempts:
            return AuthResult(
                status=AuthStatus.INVALID,
                error_message="Too many authentication attempts"
            )
        
        try:
            # Wait for authentication message
            message = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=self.config.auth_timeout
            )
            
            if message.get("type") != "auth":
                return AuthResult(
                    status=AuthStatus.UNAUTHENTICATED,
                    error_message="Authentication message expected"
                )
            
            # Attempt authentication
            auth_data = message.get("data", {})
            result = await self.authenticator.authenticate(websocket, auth_data)
            
            if result.status == AuthStatus.AUTHENTICATED:
                self._authenticated_connections[connection_id] = result
                await websocket.send_json({
                    "type": "auth_success",
                    "data": {
                        "user_id": result.user_id,
                        "expires_at": result.expires_at.isoformat() if result.expires_at else None
                    }
                })
            else:
                # Increment auth attempts
                self._auth_attempts[connection_id] = attempts + 1
                await websocket.send_json({
                    "type": "auth_error",
                    "data": {
                        "error": result.error_message,
                        "status": result.status.value
                    }
                })
            
            return result
            
        except asyncio.TimeoutError:
            return AuthResult(
                status=AuthStatus.UNAUTHENTICATED,
                error_message="Authentication timeout"
            )
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return AuthResult(
                status=AuthStatus.INVALID,
                error_message="Authentication failed"
            )
    
    def is_authenticated(self, connection_id: str) -> bool:
        """Check if connection is authenticated."""
        return connection_id in self._authenticated_connections
    
    def get_auth_data(self, connection_id: str) -> Optional[AuthResult]:
        """Get authentication data for connection."""
        return self._authenticated_connections.get(connection_id)
    
    def remove_connection(self, connection_id: str) -> None:
        """Remove connection from authenticated list."""
        self._authenticated_connections.pop(connection_id, None)
        self._auth_attempts.pop(connection_id, None)

class WebSocketAuthHandler:
    """
    Handler for WebSocket authentication events.
    
    Provides decorators for authentication-required handlers.
    """
    
    def __init__(self, middleware: WebSocketAuthMiddleware):
        self.middleware = middleware
    
    def require_auth(self, handler: Callable) -> Callable:
        """Decorator to require authentication for WebSocket handlers."""
        async def wrapper(websocket: WebSocketConnection, message: Dict[str, Any]):
            if not self.middleware.is_authenticated(websocket.connection_id):
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "error": "Authentication required",
                        "code": "AUTH_REQUIRED"
                    }
                })
                return
            
            return await handler(websocket, message)
        
        return wrapper
    
    def optional_auth(self, handler: Callable) -> Callable:
        """Decorator for optional authentication."""
        async def wrapper(websocket: WebSocketConnection, message: Dict[str, Any]):
            # Add auth data to message if available
            auth_data = self.middleware.get_auth_data(websocket.connection_id)
            if auth_data:
                message["auth"] = {
                    "user_id": auth_data.user_id,
                    "user_data": auth_data.user_data
                }
            
            return await handler(websocket, message)
        
        return wrapper

# Factory for creating authenticators
class AuthenticatorFactory:
    """Factory for creating different types of authenticators."""
    
    @staticmethod
    def create_jwt_authenticator(config: AuthConfig) -> JWTAuthenticator:
        """Create JWT authenticator."""
        return JWTAuthenticator(config)
    
    @staticmethod
    def create_auth_middleware(authenticator: WebSocketAuthenticator, config: AuthConfig) -> WebSocketAuthMiddleware:
        """Create authentication middleware."""
        return WebSocketAuthMiddleware(authenticator, config)
    
    @staticmethod
    def create_auth_handler(middleware: WebSocketAuthMiddleware) -> WebSocketAuthHandler:
        """Create authentication handler."""
        return WebSocketAuthHandler(middleware) 