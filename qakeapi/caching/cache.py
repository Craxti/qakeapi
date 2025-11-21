"""
Caching system for the framework.

This module provides in-memory caching with TTL support.
"""

import time
from threading import Lock
from typing import Any, Dict, Optional


class Cache:
    """
    Base cache class.

    Provides interface for caching operations.
    """

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        raise NotImplementedError

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        raise NotImplementedError

    def delete(self, key: str) -> None:
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        raise NotImplementedError

    def clear(self) -> None:
        """Clear all cache entries."""
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and not expired
        """
        return self.get(key) is not None


class CacheEntry:
    """Represents a cache entry with expiration."""

    def __init__(self, value: Any, expires_at: Optional[float] = None):
        """
        Initialize cache entry.

        Args:
            value: Cached value
            expires_at: Expiration timestamp (None for no expiration)
        """
        self.value = value
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        """
        Check if entry is expired.

        Returns:
            True if expired
        """
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class MemoryCache(Cache):
    """
    In-memory cache implementation.

    Thread-safe cache with TTL support.
    """

    def __init__(self, default_ttl: Optional[int] = None):
        """
        Initialize memory cache.

        Args:
            default_ttl: Default TTL in seconds
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return None

            # Check expiration
            if entry.is_expired():
                # Remove expired entry
                self._cache.pop(key, None)
                return None

            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set value in cache."""
        with self._lock:
            # Use provided TTL or default
            ttl = ttl if ttl is not None else self.default_ttl

            # Calculate expiration
            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl

            # Store entry
            self._cache[key] = CacheEntry(value, expires_at)

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of removed entries
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]

            for key in expired_keys:
                self._cache.pop(key, None)

            return len(expired_keys)

    def size(self) -> int:
        """
        Get number of cache entries.

        Returns:
            Number of entries
        """
        with self._lock:
            return len(self._cache)


class CacheManager:
    """
    Cache manager for managing multiple cache instances.
    """

    def __init__(self, default_cache: Optional[Cache] = None):
        """
        Initialize cache manager.

        Args:
            default_cache: Default cache instance
        """
        self.default_cache = default_cache or MemoryCache()
        self._caches: Dict[str, Cache] = {}

    def get_cache(self, name: str = "default") -> Cache:
        """
        Get cache instance by name.

        Args:
            name: Cache name

        Returns:
            Cache instance
        """
        if name == "default":
            return self.default_cache

        if name not in self._caches:
            self._caches[name] = MemoryCache()

        return self._caches[name]

    def add_cache(self, name: str, cache: Cache) -> None:
        """
        Add cache instance.

        Args:
            name: Cache name
            cache: Cache instance
        """
        self._caches[name] = cache
