"""
Rate limiting implementation.

This module provides rate limiting to prevent abuse.
"""

import time
from typing import Any, Callable, Dict, Optional, Tuple
from collections import defaultdict
from threading import Lock
from qakeapi.core.middleware import BaseMiddleware


class RateLimiter:
    """
    Rate limiter using token bucket algorithm.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
            requests_per_hour: Maximum requests per hour
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Store request timestamps
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
    
    def _cleanup_old_requests(self, key: str) -> None:
        """
        Remove old request timestamps.
        
        Args:
            key: Rate limit key (e.g., IP address)
        """
        current_time = time.time()
        
        # Clean minute requests (older than 60 seconds)
        self.minute_requests[key] = [
            ts for ts in self.minute_requests[key]
            if current_time - ts < 60
        ]
        
        # Clean hour requests (older than 3600 seconds)
        self.hour_requests[key] = [
            ts for ts in self.hour_requests[key]
            if current_time - ts < 3600
        ]
    
    def is_allowed(self, key: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request is allowed.
        
        Args:
            key: Rate limit key (e.g., IP address)
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        with self.lock:
            self._cleanup_old_requests(key)
            
            current_time = time.time()
            
            # Check minute limit
            minute_count = len(self.minute_requests[key])
            if minute_count >= self.requests_per_minute:
                # Calculate retry after
                oldest = min(self.minute_requests[key])
                retry_after = int(60 - (current_time - oldest)) + 1
                return False, retry_after
            
            # Check hour limit
            hour_count = len(self.hour_requests[key])
            if hour_count >= self.requests_per_hour:
                # Calculate retry after
                oldest = min(self.hour_requests[key])
                retry_after = int(3600 - (current_time - oldest)) + 1
                return False, retry_after
            
            # Add current request
            self.minute_requests[key].append(current_time)
            self.hour_requests[key].append(current_time)
            
            return True, None
    
    def reset(self, key: str) -> None:
        """
        Reset rate limit for a key.
        
        Args:
            key: Rate limit key
        """
        with self.lock:
            self.minute_requests.pop(key, None)
            self.hour_requests.pop(key, None)


class RateLimitMiddleware(BaseMiddleware):
    """
    Rate limiting middleware.
    """
    
    def __init__(
        self,
        app: Any = None,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        key_func: Optional[Callable] = None,
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            app: ASGI application
            requests_per_minute: Maximum requests per minute
            requests_per_hour: Maximum requests per hour
            key_func: Function to extract rate limit key from request
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_minute, requests_per_hour)
        self.key_func = key_func or self._default_key_func
    
    def _default_key_func(self, scope: Dict[str, Any]) -> str:
        """
        Default function to extract rate limit key.
        
        Args:
            scope: ASGI scope
            
        Returns:
            Rate limit key (IP address)
        """
        client = scope.get("client")
        if client:
            return client[0]  # IP address
        return "unknown"
    
    async def process_http(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """
        Process HTTP request with rate limiting.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Get rate limit key
        key = self.key_func(scope)
        
        # Check rate limit
        is_allowed, retry_after = self.rate_limiter.is_allowed(key)
        
        if not is_allowed:
            # Rate limit exceeded
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"retry-after", str(retry_after).encode()],
                ],
            })
            await send({
                "type": "http.response.body",
                "body": b'{"detail": "Rate limit exceeded"}',
            })
            return
        
        # Process request
        if self.app:
            await self.app(scope, receive, send)
