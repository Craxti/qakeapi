"""
Cache middleware for response caching.

This module provides middleware for caching HTTP responses.
"""

import hashlib
from typing import Any, Dict, Optional
from qakeapi.core.middleware import BaseMiddleware
from qakeapi.core.response import Response, JSONResponse
from .cache import Cache, MemoryCache


class CacheMiddleware(BaseMiddleware):
    """
    Middleware for caching HTTP responses.
    """

    def __init__(
        self,
        app: Any = None,
        cache: Optional[Cache] = None,
        ttl: int = 300,
        key_prefix: str = "cache:",
        cacheable_methods: Optional[list] = None,
        cacheable_status_codes: Optional[list] = None,
    ):
        """
        Initialize cache middleware.

        Args:
            app: ASGI application
            cache: Cache instance (defaults to MemoryCache)
            ttl: Default TTL in seconds
            key_prefix: Prefix for cache keys
            cacheable_methods: List of cacheable HTTP methods
            cacheable_status_codes: List of cacheable status codes
        """
        super().__init__(app)
        self.cache = cache or MemoryCache()
        self.ttl = ttl
        self.key_prefix = key_prefix
        self.cacheable_methods = cacheable_methods or ["GET"]
        self.cacheable_status_codes = cacheable_status_codes or [200]

    def _generate_cache_key(
        self,
        method: str,
        path: str,
        query_string: bytes,
        headers: Dict[str, str],
    ) -> str:
        """
        Generate cache key from request.

        Args:
            method: HTTP method
            path: Request path
            query_string: Query string
            headers: Request headers

        Returns:
            Cache key
        """
        # Include method, path, and query string
        key_parts = [method, path]

        if query_string:
            key_parts.append(query_string.decode())

        # Include relevant headers (e.g., Accept, Accept-Language)
        relevant_headers = ["accept", "accept-language", "authorization"]
        for header_name in relevant_headers:
            if header_name in headers:
                key_parts.append(f"{header_name}:{headers[header_name]}")

        # Create hash
        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()

        return f"{self.key_prefix}{key_hash}"

    async def process_http(
        self, scope: Dict[str, Any], receive: Any, send: Any
    ) -> None:
        """
        Process HTTP request with caching.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        method = scope.get("method", "GET")

        # Only cache GET requests by default
        if method not in self.cacheable_methods:
            if self.app:
                await self.app(scope, receive, send)
            return

        # Get request details
        path = scope.get("path", "/")
        query_string = scope.get("query_string", b"")
        headers = {}
        for key, value in scope.get("headers", []):
            headers[key.decode().lower()] = value.decode()

        # Generate cache key
        cache_key = self._generate_cache_key(method, path, query_string, headers)

        # Try to get from cache
        cached_response = self.cache.get(cache_key)

        if cached_response is not None:
            # Send cached response
            await send(
                {
                    "type": "http.response.start",
                    "status": cached_response["status"],
                    "headers": cached_response["headers"],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": cached_response["body"],
                }
            )
            return

        # Cache miss - process request and cache response
        response_data = {
            "status": None,
            "headers": None,
            "body": None,
        }

        async def send_wrapper(message: Dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                response_data["status"] = message["status"]
                response_data["headers"] = message["headers"]
            elif message["type"] == "http.response.body":
                response_data["body"] = message.get("body", b"")

            await send(message)

        if self.app:
            await self.app(scope, receive, send_wrapper)

        # Cache response if status code is cacheable
        if (
            response_data["status"] in self.cacheable_status_codes
            and response_data["body"] is not None
        ):
            self.cache.set(
                cache_key,
                {
                    "status": response_data["status"],
                    "headers": response_data["headers"],
                    "body": response_data["body"],
                },
                ttl=self.ttl,
            )
