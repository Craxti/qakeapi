"""
Authentication system.

This module provides authentication helpers and middleware.
"""

from typing import Optional, Dict, Any, Callable
from .jwt import JWTManager, JWTError
from .password import PasswordHasher, hash_password, verify_password


class AuthManager:
    """
    Authentication manager.
    
    Handles user authentication, token generation, and verification.
    """
    
    def __init__(self, secret_key: str, token_expires_in: int = 3600):
        """
        Initialize auth manager.
        
        Args:
            secret_key: Secret key for JWT tokens
            token_expires_in: Token expiration time in seconds
        """
        self.jwt_manager = JWTManager(secret_key)
        self.password_hasher = PasswordHasher()
        self.token_expires_in = token_expires_in
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Create access token.
        
        Args:
            data: Token payload data
            
        Returns:
            JWT token string
        """
        return self.jwt_manager.encode(
            data,
            expires_in=self.token_expires_in
        )
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload or None if invalid
        """
        try:
            return self.jwt_manager.decode(token)
        except JWTError:
            return None
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return self.password_hasher.hash(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify a password.
        
        Args:
            password: Plain text password
            hashed: Hashed password
            
        Returns:
            True if password matches
        """
        return self.password_hasher.verify(password, hashed)


def get_token_from_header(authorization: Optional[str]) -> Optional[str]:
    """
    Extract token from Authorization header.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Token string or None
    """
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2:
        return None
    
    scheme, token = parts
    if scheme.lower() != "bearer":
        return None
    
    return token

