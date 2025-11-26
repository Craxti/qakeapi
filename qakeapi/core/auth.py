"""
Authentication and Authorization for QakeAPI.

This module provides:
- JWT tokens (creation and verification)
- Session management
- @require_auth and @require_role decorators
- Middleware for automatic token verification
"""

import base64
import hashlib
import hmac
import inspect
import json
import time
from typing import Any, Callable, Dict, List, Optional, Set
from functools import wraps

from .exceptions import UnauthorizedError, ForbiddenError
from .request import Request
from .response import JSONResponse


# JWT Implementation (using standard library only)

class JWTManager:
    """JWT token manager."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", expiration: int = 3600):
        """
        Initialize JWT manager.
        
        Args:
            secret_key: Secret key for token signing
            algorithm: Signing algorithm (default: HS256)
            expiration: Token lifetime in seconds (default: 1 hour)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration = expiration
    
    def encode(self, payload: Dict[str, Any], expires_in: Optional[int] = None) -> str:
        """
        Create JWT token.
        
        Args:
            payload: Data to include in token
            expires_in: Token lifetime in seconds (if not specified, uses self.expiration)
            
        Returns:
            Encoded JWT token
        """
        expires_in = expires_in or self.expiration
        exp = int(time.time()) + expires_in
        
        header = {
            "alg": self.algorithm,
            "typ": "JWT"
        }
        
        payload_with_exp = {
            **payload,
            "exp": exp,
            "iat": int(time.time())
        }
        
        # Base64 encode header and payload
        header_b64 = base64.urlsafe_b64encode(
            json.dumps(header, separators=(',', ':')).encode()
        ).decode().rstrip('=')
        
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload_with_exp, separators=(',', ':')).encode()
        ).decode().rstrip('=')
        
        # Create signature
        message = f"{header_b64}.{payload_b64}".encode()
        signature = hmac.new(
            self.secret_key.encode(),
            message,
            hashlib.sha256
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"
    
    def decode(self, token: str) -> Dict[str, Any]:
        """
        Decode and verify JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            Decoded token payload
            
        Raises:
            UnauthorizedError: If token is invalid or expired
        """
        try:
            parts = token.split('.')
            if len(parts) != 3:
                raise UnauthorizedError("Invalid token format")
            
            header_b64, payload_b64, signature_b64 = parts
            
            # Verify signature
            message = f"{header_b64}.{payload_b64}".encode()
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message,
                hashlib.sha256
            ).digest()
            expected_signature_b64 = base64.urlsafe_b64encode(expected_signature).decode().rstrip('=')
            
            # Add padding if needed for comparison
            def add_padding(s):
                return s + '=' * (4 - len(s) % 4) if len(s) % 4 else s
            
            if not hmac.compare_digest(
                add_padding(signature_b64),
                add_padding(expected_signature_b64)
            ):
                raise UnauthorizedError("Invalid token signature")
            
            # Decode payload
            payload_b64_padded = add_padding(payload_b64)
            payload_json = base64.urlsafe_b64decode(payload_b64_padded).decode()
            payload = json.loads(payload_json)
            
            # Check expiration
            if "exp" in payload:
                if int(time.time()) > payload["exp"]:
                    raise UnauthorizedError("Token expired")
            
            return payload
            
        except (ValueError, json.JSONDecodeError, base64.binascii.Error) as e:
            raise UnauthorizedError(f"Token decoding error: {str(e)}")


# Session Management

class SessionManager:
    """Session manager."""
    
    def __init__(self, session_timeout: int = 3600):
        """
        Initialize session manager.
        
        Args:
            session_timeout: Session lifetime in seconds (default: 1 hour)
        """
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_timestamps: Dict[str, float] = {}
        self.session_timeout = session_timeout
    
    def create_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """
        Create session.
        
        Args:
            session_id: Session ID
            data: Session data
        """
        self._sessions[session_id] = data
        self._session_timestamps[session_id] = time.time()
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if session not found or expired
        """
        if session_id not in self._sessions:
            return None
        
        # Check if session expired
        if session_id in self._session_timestamps:
            elapsed = time.time() - self._session_timestamps[session_id]
            if elapsed > self.session_timeout:
                self.delete_session(session_id)
                return None
        
        return self._sessions.get(session_id)
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """
        Update session data.
        
        Args:
            session_id: Session ID
            data: New session data
        """
        if session_id in self._sessions:
            self._sessions[session_id].update(data)
            self._session_timestamps[session_id] = time.time()
    
    def delete_session(self, session_id: str) -> None:
        """
        Delete session.
        
        Args:
            session_id: Session ID
        """
        self._sessions.pop(session_id, None)
        self._session_timestamps.pop(session_id, None)
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of deleted sessions
        """
        current_time = time.time()
        expired = [
            sid for sid, timestamp in self._session_timestamps.items()
            if current_time - timestamp > self.session_timeout
        ]
        
        for sid in expired:
            self.delete_session(sid)
        
        return len(expired)


# Global instances (can be configured)
_default_jwt_manager: Optional[JWTManager] = None
_default_session_manager: Optional[SessionManager] = None


def init_auth(secret_key: str, jwt_expiration: int = 3600, session_timeout: int = 3600) -> None:
    """
    Initialize authentication system.
    
    Args:
        secret_key: Secret key for JWT tokens
        jwt_expiration: JWT token lifetime in seconds
        session_timeout: Session lifetime in seconds
    """
    global _default_jwt_manager, _default_session_manager
    
    _default_jwt_manager = JWTManager(secret_key, expiration=jwt_expiration)
    _default_session_manager = SessionManager(session_timeout=session_timeout)


def get_jwt_manager() -> JWTManager:
    """Get global JWT manager."""
    if _default_jwt_manager is None:
        raise RuntimeError(
            "JWT manager not initialized. Call init_auth() before use."
        )
    return _default_jwt_manager


def get_session_manager() -> SessionManager:
    """Get global session manager."""
    if _default_session_manager is None:
        raise RuntimeError(
            "Session manager not initialized. Call init_auth() before use."
        )
    return _default_session_manager


# Authentication Decorators

def require_auth(
    get_user: Optional[Callable[[Dict[str, Any]], Any]] = None,
    token_location: str = "header",
    token_key: str = "authorization",
    token_prefix: str = "Bearer ",
):
    """
    Decorator for authentication verification.
    
    Args:
        get_user: Function to get user by token payload (optional)
        token_location: Where to look for token ("header" or "cookie")
        token_key: Token key (header name or cookie name)
        token_prefix: Token prefix (e.g., "Bearer ")
        
    Example:
        ```python
        @app.get("/profile")
        @require_auth()
        async def get_profile(request: Request, user: dict):
            return {"user": user}
        ```
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get token
            token = None
            
            if token_location == "header":
                auth_header = request.headers.get(token_key.lower(), "")
                if auth_header.startswith(token_prefix):
                    token = auth_header[len(token_prefix):].strip()
            elif token_location == "cookie":
                # Get cookies from request
                cookies = {}
                cookie_header = request.headers.get("cookie", "")
                if cookie_header:
                    for item in cookie_header.split(";"):
                        if "=" in item:
                            key, value = item.strip().split("=", 1)
                            cookies[key] = value
                token = cookies.get(token_key)
            
            if not token:
                raise UnauthorizedError("Token not provided")
            
            # Decode token
            jwt_manager = get_jwt_manager()
            try:
                payload = jwt_manager.decode(token)
            except UnauthorizedError:
                raise
            
            # Get user if function provided
            user = payload
            if get_user:
                try:
                    user = get_user(payload)
                    if user is None:
                        raise UnauthorizedError("User not found")
                except Exception as e:
                    raise UnauthorizedError(f"Error getting user: {str(e)}")
            
            # Add user to kwargs
            kwargs["user"] = user
            kwargs["auth_payload"] = payload
            
            # Call original function
            if inspect.iscoroutinefunction(func):
                return await func(request, *args, **kwargs)
            else:
                return func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


def require_role(*roles: str):
    """
    Decorator for user role verification.
    
    Must be used after @require_auth.
    
    Args:
        *roles: List of allowed roles
        
    Example:
        ```python
        @app.get("/admin")
        @require_auth()
        @require_role("admin", "superadmin")
        async def admin_panel(request: Request, user: dict):
            return {"message": "Welcome, admin!"}
        ```
    """
    allowed_roles = set(roles)
    
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get user from kwargs (set by require_auth)
            user = kwargs.get("user")
            auth_payload = kwargs.get("auth_payload")
            
            if not user and not auth_payload:
                raise UnauthorizedError("User not authenticated. Use @require_auth before @require_role")
            
            # Get user roles
            user_roles = []
            if isinstance(user, dict):
                user_roles = user.get("roles", []) or user.get("role", [])
            elif hasattr(user, "roles"):
                user_roles = user.roles if isinstance(user.roles, (list, set)) else [user.roles]
            elif hasattr(user, "role"):
                user_roles = [user.role] if user.role else []
            
            # Also check in payload
            if not user_roles and auth_payload:
                user_roles = auth_payload.get("roles", []) or auth_payload.get("role", [])
            
            # Convert to set for easier comparison
            if not isinstance(user_roles, (list, set)):
                user_roles = [user_roles]
            user_roles_set = set(user_roles)
            
            # Check if user has required role
            if not user_roles_set.intersection(allowed_roles):
                raise ForbiddenError(
                    f"Access forbidden. Required roles: {', '.join(allowed_roles)}"
                )
            
            # Call original function
            if inspect.iscoroutinefunction(func):
                return await func(request, *args, **kwargs)
            else:
                return func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


# Helper functions

def create_token(payload: Dict[str, Any], expires_in: Optional[int] = None) -> str:
    """
    Create JWT token.
    
    Args:
        payload: Token data
        expires_in: Lifetime in seconds
        
    Returns:
        JWT token
    """
    return get_jwt_manager().encode(payload, expires_in)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Token payload
    """
    return get_jwt_manager().decode(token)


def create_session(session_id: str, data: Dict[str, Any]) -> None:
    """
    Create session.
    
    Args:
        session_id: Session ID
        data: Session data
    """
    get_session_manager().create_session(session_id, data)


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get session data.
    
    Args:
        session_id: Session ID
        
    Returns:
        Session data or None
    """
    return get_session_manager().get_session(session_id)


def delete_session(session_id: str) -> None:
    """
    Delete session.
    
    Args:
        session_id: Session ID
    """
    get_session_manager().delete_session(session_id)
