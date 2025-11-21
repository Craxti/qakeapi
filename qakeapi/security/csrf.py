"""
CSRF (Cross-Site Request Forgery) protection.

This module provides CSRF token generation and verification.
"""

import secrets
import hmac
import hashlib
from typing import Optional, Dict
from datetime import datetime, timedelta


class CSRFProtection:
    """
    CSRF protection handler.
    """
    
    def __init__(self, secret_key: str, token_age: int = 3600):
        """
        Initialize CSRF protection.
        
        Args:
            secret_key: Secret key for token signing
            token_age: Token age in seconds
        """
        self.secret_key = secret_key
        self.token_age = token_age
    
    def generate_token(self, session_id: Optional[str] = None) -> str:
        """
        Generate CSRF token.
        
        Args:
            session_id: Optional session ID
            
        Returns:
            CSRF token string
        """
        # Generate random token
        token = secrets.token_urlsafe(32)
        
        # Create timestamp
        timestamp = int(datetime.utcnow().timestamp())
        
        # Create payload
        payload = f"{token}:{timestamp}"
        if session_id:
            payload = f"{payload}:{session_id}"
        
        # Sign payload
        signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Return token with signature
        return f"{token}:{timestamp}:{signature}"
    
    def verify_token(
        self,
        token: str,
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Verify CSRF token.
        
        Args:
            token: CSRF token string
            session_id: Optional session ID
            
        Returns:
            True if token is valid
        """
        try:
            parts = token.split(":")
            if len(parts) < 3:
                return False
            
            token_part, timestamp_str, signature = parts
            
            # Check timestamp
            timestamp = int(timestamp_str)
            age = int(datetime.utcnow().timestamp()) - timestamp
            if age > self.token_age:
                return False
            
            # Recreate payload
            payload = f"{token_part}:{timestamp}"
            if session_id:
                payload = f"{payload}:{session_id}"
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        
        except (ValueError, IndexError):
            return False
