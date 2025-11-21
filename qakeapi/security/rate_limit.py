"""
Rate limiting implementation.

This module provides rate limiting to prevent abuse.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Dict, Optional, Tuple

from qakeapi.core.middleware import BaseMiddleware


@dataclass
class RateLimitInfo:
    """Rate limit information."""

    remaining: int
    limit: int
    reset_time: Optional[int] = None


class InMemoryRateLimiter:
    """
    In-memory rate limiter with async interface for compatibility.
    """

    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize in-memory rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
        """
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()

    async def is_allowed(self, key: str) -> Tuple[bool, RateLimitInfo]:
        """
        Check if request is allowed.

        Args:
            key: Rate limit key

        Returns:
            Tuple of (is_allowed, RateLimitInfo)
        """
        with self.lock:
            current_time = time.time()
            # Clean old requests (older than 60 seconds)
            self.requests[key] = [
                ts for ts in self.requests[key] if current_time - ts < 60
            ]

            current_count = len(self.requests[key])
            allowed = current_count < self.requests_per_minute
            remaining = max(
                0, self.requests_per_minute - current_count - (1 if allowed else 0)
            )

            return allowed, RateLimitInfo(
                remaining=remaining,
                limit=self.requests_per_minute,
                reset_time=int(current_time + 60),
            )

    async def update(self, key: str) -> None:
        """
        Update rate limit counter for a key.

        Args:
            key: Rate limit key
        """
        with self.lock:
            current_time = time.time()
            # Clean old requests
            self.requests[key] = [
                ts for ts in self.requests[key] if current_time - ts < 60
            ]
            # Add current request
            self.requests[key].append(current_time)


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
            ts for ts in self.minute_requests[key] if current_time - ts < 60
        ]

        # Clean hour requests (older than 3600 seconds)
        self.hour_requests[key] = [
            ts for ts in self.hour_requests[key] if current_time - ts < 3600
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
        rate_limiter: Any = None,
        app: Any = None,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        key_func: Optional[Callable] = None,
    ):
        """
        Initialize rate limit middleware.

        Args:
            rate_limiter: Optional rate limiter instance (InMemoryRateLimiter or RateLimiter)
            app: ASGI application
            requests_per_minute: Maximum requests per minute (used if rate_limiter not provided)
            requests_per_hour: Maximum requests per hour (used if rate_limiter not provided)
            key_func: Function to extract rate limit key from request
        """
        super().__init__(app)
        if rate_limiter is not None:
            self.rate_limiter = rate_limiter
            self._is_async = hasattr(
                rate_limiter, "is_allowed"
            ) and asyncio.iscoroutinefunction(getattr(rate_limiter, "is_allowed", None))
        else:
            self.rate_limiter = RateLimiter(requests_per_minute, requests_per_hour)
            self._is_async = False
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
        if self._is_async:
            # Async rate limiter (InMemoryRateLimiter)
            is_allowed, info = await self.rate_limiter.is_allowed(key)
            if not is_allowed:
                retry_after = (
                    info.reset_time - int(time.time()) if info.reset_time else 60
                )
            else:
                retry_after = None
                # Update rate limiter
                await self.rate_limiter.update(key)
        else:
            # Sync rate limiter (RateLimiter)
            is_allowed, retry_after = self.rate_limiter.is_allowed(key)

        if not is_allowed:
            # Rate limit exceeded
            headers = [[b"content-type", b"application/json"]]
            if retry_after is not None:
                headers.append([b"retry-after", str(retry_after).encode()])
            if self._is_async:
                headers.append([b"x-ratelimit-limit", str(info.limit).encode()])
                headers.append([b"x-ratelimit-remaining", str(info.remaining).encode()])

            await send(
                {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": headers,
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"detail": "Rate limit exceeded"}',
                }
            )
            return

        # Process request
        if self.app:
            await self.app(scope, receive, send)

    async def __call__(self, request: Any, handler: Callable) -> Any:
        """
        Callable interface for middleware (for testing compatibility).

        Args:
            request: Request object
            handler: Next handler in chain

        Returns:
            Response object
        """
        # Extract key from request
        # Try calling key_func with request first, then fall back to scope
        try:
            key = self.key_func(request)
        except (TypeError, AttributeError):
            # Fall back to scope if request doesn't work
            if hasattr(request, "scope"):
                try:
                    key = self.key_func(request.scope)
                except Exception:
                    key = self._default_key_func(request.scope)
            elif hasattr(request, "client"):
                key = request.client[0] if request.client else "unknown"
            else:
                key = "unknown"

        # Check rate limit
        if self._is_async:
            # Async rate limiter (InMemoryRateLimiter)
            is_allowed, info = await self.rate_limiter.is_allowed(key)
            if not is_allowed:
                # Rate limit exceeded
                from qakeapi.core.responses import JSONResponse

                response = JSONResponse(
                    {"detail": "Rate limit exceeded"},
                    status_code=429,
                    headers={
                        "X-RateLimit-Limit": str(info.limit),
                        "X-RateLimit-Remaining": str(info.remaining),
                    },
                )
                return response
            else:
                # Update rate limiter
                await self.rate_limiter.update(key)
                # Add headers to response
                response = await handler(request)
                if hasattr(response, "set_header"):
                    response.set_header("X-RateLimit-Limit", str(info.limit))
                    response.set_header("X-RateLimit-Remaining", str(info.remaining))
                    if hasattr(info, "reset_time") and info.reset_time:
                        response.set_header(
                            "X-RateLimit-Reset", str(int(info.reset_time))
                        )
                elif hasattr(response, "headers"):
                    # Fallback для старых версий
                    if isinstance(response.headers, dict):
                        response.headers["X-RateLimit-Limit"] = str(info.limit)
                        response.headers["X-RateLimit-Remaining"] = str(info.remaining)
                    elif isinstance(response.headers, list):
                        # Добавляем заголовки в список
                        response.headers.append(
                            (b"X-RateLimit-Limit", str(info.limit).encode())
                        )
                        response.headers.append(
                            (b"X-RateLimit-Remaining", str(info.remaining).encode())
                        )
                return response
        else:
            # Sync rate limiter (RateLimiter)
            is_allowed, retry_after = self.rate_limiter.is_allowed(key)
            if not is_allowed:
                # Rate limit exceeded
                from qakeapi.core.responses import JSONResponse

                headers = {}
                if retry_after is not None:
                    headers["Retry-After"] = str(retry_after)
                return JSONResponse(
                    {"detail": "Rate limit exceeded"}, status_code=429, headers=headers
                )
            else:
                # Request allowed, continue
                return await handler(request)
