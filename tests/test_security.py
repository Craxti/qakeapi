"""
Tests for security module.
"""

import pytest
import time
from datetime import timedelta
from qakeapi.security import (
    JWTManager,
    JWTError,
    PasswordHasher,
    hash_password,
    verify_password,
    AuthManager,
    CSRFProtection,
    RateLimiter,
)


def test_jwt_encode_decode():
    """Test JWT encoding and decoding."""
    manager = JWTManager("secret-key")

    payload = {"user_id": 123, "username": "test"}
    token = manager.encode(payload)

    assert token is not None
    assert len(token.split(".")) == 3

    decoded = manager.decode(token)
    assert decoded["user_id"] == 123
    assert decoded["username"] == "test"


def test_jwt_expiration():
    """Test JWT token expiration."""
    manager = JWTManager("secret-key")

    # Create token with expiration
    payload = {"user_id": 123}
    token = manager.encode(payload, expires_in=3600)  # 1 hour

    # Should decode immediately
    decoded = manager.decode(token)
    assert decoded["user_id"] == 123
    assert "exp" in decoded
    assert "iat" in decoded

    # Test that expired token fails (create one that's already expired)
    expired_payload = {"user_id": 123}
    expired_token = manager.encode(expired_payload, expires_delta=timedelta(seconds=-1))

    with pytest.raises(JWTError):
        manager.decode(expired_token)


def test_jwt_invalid_token():
    """Test JWT with invalid token."""
    manager = JWTManager("secret-key")

    with pytest.raises(JWTError):
        manager.decode("invalid.token.here")

    with pytest.raises(JWTError):
        manager.decode("not.enough.parts.here.extra")


def test_password_hashing():
    """Test password hashing."""
    password = "test_password_123"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("pbkdf2_sha256$")

    # Verify correct password
    assert verify_password(password, hashed) is True

    # Verify incorrect password
    assert verify_password("wrong_password", hashed) is False


def test_password_hasher():
    """Test PasswordHasher class."""
    hasher = PasswordHasher()

    password = "test123"
    hashed = hasher.hash(password)

    assert hasher.verify(password, hashed) is True
    assert hasher.verify("wrong", hashed) is False


def test_auth_manager():
    """Test AuthManager."""
    manager = AuthManager("secret-key", token_expires_in=3600)

    # Test password hashing
    password = "test123"
    hashed = manager.hash_password(password)
    assert manager.verify_password(password, hashed) is True

    # Test token creation
    payload = {"user_id": 123}
    token = manager.create_access_token(payload)
    assert token is not None
    assert len(token) > 0
    assert "." in token  # JWT format

    # Test token verification through manager
    decoded = manager.verify_token(token)
    assert decoded is not None
    assert "user_id" in decoded
    assert decoded["user_id"] == 123

    # Test invalid token
    assert manager.verify_token("invalid.token.here") is None


def test_csrf_protection():
    """Test CSRF protection."""
    protection = CSRFProtection("secret-key")

    # Generate token
    token = protection.generate_token()
    assert token is not None

    # Verify token
    assert protection.verify_token(token) is True

    # Verify with session
    session_id = "session123"
    token2 = protection.generate_token(session_id)
    assert protection.verify_token(token2, session_id) is True
    assert protection.verify_token(token2) is False  # Wrong session

    # Test expired token
    protection_short = CSRFProtection("secret-key", token_age=1)
    token3 = protection_short.generate_token()
    time.sleep(2)
    assert protection_short.verify_token(token3) is False


def test_rate_limiter():
    """Test RateLimiter."""
    limiter = RateLimiter(requests_per_minute=2, requests_per_hour=10)

    key = "test_key"

    # First request should be allowed
    allowed, retry_after = limiter.is_allowed(key)
    assert allowed is True
    assert retry_after is None

    # Second request should be allowed
    allowed, retry_after = limiter.is_allowed(key)
    assert allowed is True

    # Third request should be blocked
    allowed, retry_after = limiter.is_allowed(key)
    assert allowed is False
    assert retry_after is not None

    # Reset and try again
    limiter.reset(key)
    allowed, retry_after = limiter.is_allowed(key)
    assert allowed is True


def test_rate_limiter_different_keys():
    """Test RateLimiter with different keys."""
    limiter = RateLimiter(requests_per_minute=1)

    key1 = "key1"
    key2 = "key2"

    # Both should be allowed (different keys)
    allowed1, _ = limiter.is_allowed(key1)
    allowed2, _ = limiter.is_allowed(key2)

    assert allowed1 is True
    assert allowed2 is True

    # But second request for same key should be blocked
    allowed1, _ = limiter.is_allowed(key1)
    assert allowed1 is False
