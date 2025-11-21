"""
JWT (JSON Web Token) implementation.

This module provides JWT token generation and verification using only
Python standard library (base64, hmac, hashlib, json, time).
"""

import base64
import hmac
import hashlib
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class JWTError(Exception):
    """Base exception for JWT operations."""
    pass


class JWTManager:
    """
    JWT token manager.
    
    Handles encoding, decoding, and verification of JWT tokens.
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize JWT manager.
        
        Args:
            secret_key: Secret key for signing tokens
            algorithm: Signing algorithm (HS256, HS384, HS512)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm.upper()
        
        if self.algorithm not in ("HS256", "HS384", "HS512"):
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    def _base64url_encode(self, data: bytes) -> str:
        """
        Base64URL encode data.
        
        Args:
            data: Data to encode
            
        Returns:
            Base64URL encoded string
        """
        return base64.urlsafe_b64encode(data).decode().rstrip("=")
    
    def _base64url_decode(self, data: str) -> bytes:
        """
        Base64URL decode data.
        
        Args:
            data: Base64URL encoded string
            
        Returns:
            Decoded bytes
        """
        # Add padding if needed
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        
        return base64.urlsafe_b64decode(data)
    
    def _sign(self, message: bytes) -> bytes:
        """
        Sign message using HMAC.
        
        Args:
            message: Message to sign
            
        Returns:
            Signature bytes
        """
        # Get hash algorithm
        if self.algorithm == "HS256":
            hash_alg = hashlib.sha256
        elif self.algorithm == "HS384":
            hash_alg = hashlib.sha384
        else:  # HS512
            hash_alg = hashlib.sha512
        
        # Create HMAC signature
        signature = hmac.new(
            self.secret_key.encode(),
            message,
            hash_alg
        ).digest()
        
        return signature
    
    def encode(
        self,
        payload: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
        expires_in: Optional[int] = None,
    ) -> str:
        """
        Encode payload into JWT token.
        
        Args:
            payload: Token payload
            expires_delta: Expiration time delta
            expires_in: Expiration time in seconds
            
        Returns:
            Encoded JWT token
        """
        # Create header
        header = {
            "typ": "JWT",
            "alg": self.algorithm,
        }
        
        # Add expiration (use time.time() for consistency)
        current_time = time.time()
        if expires_delta:
            exp = datetime.utcnow() + expires_delta
            payload["exp"] = int(exp.timestamp())
        elif expires_in:
            payload["exp"] = int(current_time + expires_in)
        
        # Add issued at
        payload["iat"] = int(current_time)
        
        # Encode header and payload
        header_encoded = self._base64url_encode(
            json.dumps(header, separators=(",", ":")).encode()
        )
        payload_encoded = self._base64url_encode(
            json.dumps(payload, separators=(",", ":")).encode()
        )
        
        # Create message
        message = f"{header_encoded}.{payload_encoded}".encode()
        
        # Sign message
        signature = self._sign(message)
        signature_encoded = self._base64url_encode(signature)
        
        # Return token
        return f"{header_encoded}.{payload_encoded}.{signature_encoded}"
    
    def decode(self, token: str, verify: bool = True) -> Dict[str, Any]:
        """
        Decode and verify JWT token.
        
        Args:
            token: JWT token string
            verify: Whether to verify signature and expiration
            
        Returns:
            Decoded payload
            
        Raises:
            JWTError: If token is invalid
        """
        try:
            # Split token
            parts = token.split(".")
            if len(parts) != 3:
                raise JWTError("Invalid token format")
            
            header_encoded, payload_encoded, signature_encoded = parts
            
            # Decode header
            header_data = self._base64url_decode(header_encoded)
            header = json.loads(header_data)
            
            # Check algorithm
            if header.get("alg") != self.algorithm:
                raise JWTError(f"Algorithm mismatch: {header.get('alg')} != {self.algorithm}")
            
            # Decode payload
            payload_data = self._base64url_decode(payload_encoded)
            payload = json.loads(payload_data)
            
            if verify:
                # Verify signature
                message = f"{header_encoded}.{payload_encoded}".encode()
                expected_signature = self._base64url_encode(self._sign(message))
                
                if signature_encoded != expected_signature:
                    raise JWTError("Invalid signature")
                
                # Verify expiration
                if "exp" in payload:
                    exp = payload["exp"]
                    current_time = int(time.time())
                    if current_time >= exp:
                        raise JWTError("Token expired")
            
            return payload
        
        except (ValueError, json.JSONDecodeError, KeyError) as e:
            raise JWTError(f"Invalid token: {e}") from e

