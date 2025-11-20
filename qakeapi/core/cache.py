"""
Cache implementation for QakeAPI with support for both in-memory and Redis caching.
"""
from typing import Any, Optional, Union
from datetime import datetime, timedelta
import json
import asyncio
from functools import wraps

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class Cache:
    def __init__(self, backend: str = "memory", redis_url: Optional[str] = None):
        """
        Initialize cache with specified backend.
        
        Args:
            backend: Either "memory" or "redis"
            redis_url: Redis connection URL if using Redis backend
        """
        self._backend = backend
        self._cache = {}
        self._redis = None
        
        if backend == "redis":
            if not REDIS_AVAILABLE:
                raise ImportError("Redis support requires 'redis' package")
            if not redis_url:
                raise ValueError("redis_url is required for Redis backend")
            self._redis = aioredis.from_url(redis_url)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if self._backend == "memory":
            if key not in self._cache:
                return None
            value, expiry = self._cache[key]
            if expiry and datetime.now() > expiry:
                del self._cache[key]
                return None
            return value
        else:
            value = await self._redis.get(key)
            return json.loads(value) if value else None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> None:
        """
        Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds or timedelta
        """
        if isinstance(ttl, timedelta):
            ttl = int(ttl.total_seconds())

        if self._backend == "memory":
            expiry = datetime.now() + timedelta(seconds=ttl) if ttl else None
            self._cache[key] = (value, expiry)
        else:
            await self._redis.set(
                key,
                json.dumps(value),
                ex=ttl
            )

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        if self._backend == "memory":
            self._cache.pop(key, None)
        else:
            await self._redis.delete(key)

    async def clear(self) -> None:
        """Clear all cached values."""
        if self._backend == "memory":
            self._cache.clear()
        else:
            await self._redis.flushdb()

def cache_decorator(ttl: Optional[int] = None):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Cache TTL in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Get cache instance
            cache = Cache()
            
            # Try to get from cache
            result = await cache.get(key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator 