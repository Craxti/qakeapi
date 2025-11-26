"""
Caching system for QakeAPI.

Provides response caching functionality as a decorator for routes.
"""

import hashlib
import json
import time
from typing import Any, Callable, Dict, Optional, Tuple
from functools import wraps


class Cache:
    """
    Simple in-memory cache with TTL support.
    
    Stores cached responses with expiration timestamps.
    """
    
    def __init__(self):
        """Initialize cache."""
        # Store cache entries: {key: (value, expiry_timestamp)}
        self._cache: Dict[str, Tuple[Any, float]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists and not expired, None otherwise
        """
        if key not in self._cache:
            return None
        
        value, expiry = self._cache[key]
        
        # Check if expired
        if time.time() > expiry:
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any, ttl: int) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        now = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if now > expiry
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        now = time.time()
        total = len(self._cache)
        expired = sum(
            1 for _, expiry in self._cache.values()
            if now > expiry
        )
        active = total - expired
        
        return {
            "total_entries": total,
            "active_entries": active,
            "expired_entries": expired,
        }


# Global cache instance
_cache = Cache()


def get_cache() -> Cache:
    """Get global cache instance."""
    return _cache


def generate_cache_key(
    path: str,
    method: str,
    query_params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    include_headers: bool = False,
) -> str:
    """
    Generate cache key from request parameters.
    
    Args:
        path: Request path
        method: HTTP method
        query_params: Query parameters
        headers: Request headers
        include_headers: Whether to include headers in cache key
        
    Returns:
        Cache key string
    """
    # Base key
    key_parts = [method.upper(), path]
    
    # Add query parameters if present
    if query_params:
        # Sort for consistent keys
        sorted_params = sorted(query_params.items())
        query_str = "&".join(f"{k}={v}" for k, v in sorted_params)
        key_parts.append(query_str)
    
    # Add headers if requested
    if include_headers and headers:
        # Include specific headers that affect response
        header_keys = ["accept", "accept-language", "authorization"]
        header_parts = []
        for hkey in header_keys:
            if hkey in headers:
                header_parts.append(f"{hkey}:{headers[hkey]}")
        if header_parts:
            key_parts.append("|".join(header_parts))
    
    # Create key string
    key_string = "|".join(key_parts)
    
    # Hash for shorter keys
    return hashlib.md5(key_string.encode()).hexdigest()


def cache(
    ttl: int = 300,
    key_func: Optional[Callable[[Any], str]] = None,
    include_headers: bool = False,
):
    """
    Cache decorator for routes.
    
    Args:
        ttl: Time to live in seconds (default: 300 = 5 minutes)
        key_func: Optional function to generate custom cache key from request
        include_headers: Whether to include headers in cache key generation
        
    Returns:
        Decorator function
        
    Example:
        ```python
        @cache(ttl=60)
        @app.get("/api/data")
        def get_data():
            return {"data": "..."}
        
        # Custom cache key
        @cache(
            ttl=300,
            key_func=lambda req: f"user:{req.headers.get('user-id')}:{req.path}"
        )
        @app.get("/api/user-data")
        def get_user_data():
            return {"data": "..."}
        ```
    """
    def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
        """Apply caching to handler."""
        # Store cache config in handler
        handler._cache_config = {
            "ttl": ttl,
            "key_func": key_func,
            "include_headers": include_headers,
        }
        
        return handler
    
    return decorator

