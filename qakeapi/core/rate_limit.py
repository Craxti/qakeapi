"""
Rate limiting system for QakeAPI.

Provides rate limiting functionality as a decorator for routes.
"""

import time
from collections import defaultdict
from typing import Any, Callable, Dict, Optional, Tuple
from functools import wraps


class RateLimiter:
    """
    Rate limiter for tracking and limiting requests.
    
    Supports per-route and per-IP rate limiting.
    """
    
    def __init__(self):
        """Initialize rate limiter."""
        # Store request timestamps: {route_key: {ip: [timestamps]}}
        self._requests: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
    
    def check_rate_limit(
        self,
        route_key: str,
        client_ip: str,
        requests_per_minute: int,
        window_seconds: int = 60,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if request is within rate limit.
        
        Args:
            route_key: Unique key for the route
            client_ip: Client IP address
            requests_per_minute: Maximum requests per minute
            window_seconds: Time window in seconds (default: 60)
            
        Returns:
            Tuple of (is_allowed, error_info)
            error_info is None if allowed, dict with details if not allowed
        """
        now = time.time()
        route_requests = self._requests[route_key]
        ip_requests = route_requests[client_ip]
        
        # Clean old requests outside the window
        cutoff_time = now - window_seconds
        ip_requests[:] = [ts for ts in ip_requests if ts > cutoff_time]
        
        # Check if limit exceeded
        if len(ip_requests) >= requests_per_minute:
            # Calculate retry after
            oldest_request = min(ip_requests) if ip_requests else now
            retry_after = int(window_seconds - (now - oldest_request)) + 1
            
            return False, {
                "limit": requests_per_minute,
                "remaining": 0,
                "reset_at": now + retry_after,
                "retry_after": retry_after,
            }
        
        # Record request
        ip_requests.append(now)
        
        # Calculate remaining requests
        remaining = max(0, requests_per_minute - len(ip_requests))
        reset_at = now + window_seconds
        
        return True, {
            "limit": requests_per_minute,
            "remaining": remaining,
            "reset_at": reset_at,
        }
    
    def get_rate_limit_info(
        self,
        route_key: str,
        client_ip: str,
        requests_per_minute: int,
        window_seconds: int = 60,
    ) -> Dict[str, Any]:
        """
        Get current rate limit information without recording a request.
        
        Args:
            route_key: Unique key for the route
            client_ip: Client IP address
            requests_per_minute: Maximum requests per minute
            window_seconds: Time window in seconds
            
        Returns:
            Dictionary with rate limit information
        """
        now = time.time()
        route_requests = self._requests[route_key]
        ip_requests = route_requests.get(client_ip, [])
        
        # Clean old requests
        cutoff_time = now - window_seconds
        ip_requests = [ts for ts in ip_requests if ts > cutoff_time]
        
        remaining = max(0, requests_per_minute - len(ip_requests))
        reset_at = now + window_seconds
        
        return {
            "limit": requests_per_minute,
            "remaining": remaining,
            "reset_at": reset_at,
        }


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(
    requests_per_minute: int = 60,
    window_seconds: int = 60,
    per_ip: bool = True,
    key_func: Optional[Callable[[Any], str]] = None,
):
    """
    Rate limit decorator for routes.
    
    Args:
        requests_per_minute: Maximum number of requests per time window
        window_seconds: Time window in seconds (default: 60)
        per_ip: If True, rate limit per IP address (default: True)
        key_func: Optional function to generate custom rate limit key from request
        
    Returns:
        Decorator function
        
    Example:
        ```python
        @rate_limit(requests_per_minute=10, window_seconds=60)
        @app.get("/api/data")
        def get_data():
            return {"data": "..."}
        
        # Custom key function
        @rate_limit(
            requests_per_minute=5,
            key_func=lambda req: f"{req.path}:{req.headers.get('user-id')}"
        )
        @app.post("/api/upload")
        def upload():
            return {"status": "ok"}
        ```
    """
    def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
        """Apply rate limiting to handler."""
        # Store rate limit config in handler
        handler._rate_limit = {
            "requests_per_minute": requests_per_minute,
            "window_seconds": window_seconds,
            "per_ip": per_ip,
            "key_func": key_func,
        }
        
        return handler
    
    return decorator


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    return _rate_limiter

