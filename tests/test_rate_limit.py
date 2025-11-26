"""
Tests for rate limiting system.
"""

import pytest
import time
from qakeapi.core.rate_limit import RateLimiter, rate_limit, get_rate_limiter


class TestRateLimiter:
    """Tests for RateLimiter class."""
    
    def test_rate_limiter_creation(self):
        """Test creating a rate limiter."""
        limiter = RateLimiter()
        assert limiter._requests == {}
    
    def test_check_rate_limit_allowed(self):
        """Test rate limit check when allowed."""
        limiter = RateLimiter()
        
        is_allowed, info = limiter.check_rate_limit(
            route_key="test:route",
            client_ip="127.0.0.1",
            requests_per_minute=10,
            window_seconds=60
        )
        
        assert is_allowed is True
        assert info["limit"] == 10
        assert info["remaining"] == 9
        assert "reset_at" in info
    
    def test_check_rate_limit_exceeded(self):
        """Test rate limit check when exceeded."""
        limiter = RateLimiter()
        
        # Make requests up to limit
        for i in range(10):
            is_allowed, _ = limiter.check_rate_limit(
                route_key="test:route",
                client_ip="127.0.0.1",
                requests_per_minute=10,
                window_seconds=60
            )
            assert is_allowed is True
        
        # Next request should be blocked
        is_allowed, info = limiter.check_rate_limit(
            route_key="test:route",
            client_ip="127.0.0.1",
            requests_per_minute=10,
            window_seconds=60
        )
        
        assert is_allowed is False
        assert info["limit"] == 10
        assert info["remaining"] == 0
        assert "retry_after" in info
    
    def test_check_rate_limit_per_ip(self):
        """Test rate limiting per IP address."""
        limiter = RateLimiter()
        
        # IP 1 makes requests
        for i in range(5):
            is_allowed, _ = limiter.check_rate_limit(
                route_key="test:route",
                client_ip="127.0.0.1",
                requests_per_minute=10,
                window_seconds=60
            )
            assert is_allowed is True
        
        # IP 2 should still have full limit
        is_allowed, info = limiter.check_rate_limit(
            route_key="test:route",
            client_ip="127.0.0.2",
            requests_per_minute=10,
            window_seconds=60
        )
        
        assert is_allowed is True
        assert info["remaining"] == 9
    
    def test_check_rate_limit_cleanup_old_requests(self):
        """Test that old requests are cleaned up."""
        limiter = RateLimiter()
        
        # Make requests
        for i in range(5):
            limiter.check_rate_limit(
                route_key="test:route",
                client_ip="127.0.0.1",
                requests_per_minute=10,
                window_seconds=1  # 1 second window
            )
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be able to make more requests
        is_allowed, info = limiter.check_rate_limit(
            route_key="test:route",
            client_ip="127.0.0.1",
            requests_per_minute=10,
            window_seconds=1
        )
        
        assert is_allowed is True
        assert info["remaining"] >= 9
    
    def test_get_rate_limit_info(self):
        """Test getting rate limit info without recording request."""
        limiter = RateLimiter()
        
        # Make some requests
        for i in range(3):
            limiter.check_rate_limit(
                route_key="test:route",
                client_ip="127.0.0.1",
                requests_per_minute=10,
                window_seconds=60
            )
        
        # Get info without recording
        info = limiter.get_rate_limit_info(
            route_key="test:route",
            client_ip="127.0.0.1",
            requests_per_minute=10,
            window_seconds=60
        )
        
        assert info["limit"] == 10
        assert info["remaining"] == 7
        assert "reset_at" in info
        
        # Make another request
        limiter.check_rate_limit(
            route_key="test:route",
            client_ip="127.0.0.1",
            requests_per_minute=10,
            window_seconds=60
        )
        
        # Info should reflect new count
        info2 = limiter.get_rate_limit_info(
            route_key="test:route",
            client_ip="127.0.0.1",
            requests_per_minute=10,
            window_seconds=60
        )
        
        assert info2["remaining"] == 6


class TestRateLimitDecorator:
    """Tests for rate_limit decorator."""
    
    def test_rate_limit_decorator(self):
        """Test rate_limit decorator."""
        @rate_limit(requests_per_minute=5, window_seconds=30)
        def handler():
            return {"data": "test"}
        
        assert hasattr(handler, "_rate_limit")
        assert handler._rate_limit["requests_per_minute"] == 5
        assert handler._rate_limit["window_seconds"] == 30
        assert handler._rate_limit["per_ip"] is True
    
    def test_rate_limit_with_custom_key(self):
        """Test rate_limit with custom key function."""
        def key_func(request):
            return f"custom:{request.path}"
        
        @rate_limit(requests_per_minute=10, key_func=key_func)
        def handler():
            return {"data": "test"}
        
        assert handler._rate_limit["key_func"] == key_func
    
    def test_rate_limit_global(self):
        """Test rate_limit with per_ip=False."""
        @rate_limit(requests_per_minute=10, per_ip=False)
        def handler():
            return {"data": "test"}
        
        assert handler._rate_limit["per_ip"] is False


class TestGetRateLimiter:
    """Tests for get_rate_limiter function."""
    
    def test_get_rate_limiter(self):
        """Test getting global rate limiter."""
        limiter = get_rate_limiter()
        assert isinstance(limiter, RateLimiter)
        
        # Should return same instance
        limiter2 = get_rate_limiter()
        assert limiter is limiter2

