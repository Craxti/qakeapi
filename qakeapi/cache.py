# -*- coding: utf-8 -*-
"""
Cache module for QakeAPI.
"""
from typing import Any, Optional, Union
from functools import wraps
import json
import time
import os
from pathlib import Path

class Cache:
    """Base class for caching."""
    
    def __init__(self, backend: str = "memory", **kwargs):
        """
        Cache initialization.
        
        Args:
            backend: Backend type ('memory' or 'file')
            **kwargs: Additional parameters
        """
        self.backend = backend
        if backend == "memory":
            self._cache = {}
        elif backend == "file":
            self.cache_dir = kwargs.get('cache_dir', '.cache')
            Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        else:
            raise ValueError(f"Unsupported cache backend: {backend}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if self.backend == "memory":
            return self._get_memory(key)
        else:
            return self._get_file(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        if self.backend == "memory":
            self._set_memory(key, value, ttl)
        else:
            self._set_file(key, value, ttl)
    
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        if self.backend == "memory":
            self._delete_memory(key)
        else:
            self._delete_file(key)
    
    async def clear(self) -> None:
        """Clear all cache."""
        if self.backend == "memory":
            self._cache.clear()
        else:
            for file in Path(self.cache_dir).glob("*.cache"):
                file.unlink()
    
    def _get_memory(self, key: str) -> Optional[Any]:
        """Get value from memory."""
        if key not in self._cache:
            return None
            
        value, expire_at = self._cache[key]
        if expire_at and time.time() > expire_at:
            del self._cache[key]
            return None
            
        return value
    
    def _set_memory(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in memory."""
        expire_at = time.time() + ttl if ttl else None
        self._cache[key] = (value, expire_at)
    
    def _delete_memory(self, key: str) -> None:
        """Delete value from memory."""
        self._cache.pop(key, None)
    
    def _get_file(self, key: str) -> Optional[Any]:
        """Get value from file."""
        file_path = Path(self.cache_dir) / f"{key}.cache"
        if not file_path.exists():
            return None
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            if data['expire_at'] and time.time() > data['expire_at']:
                file_path.unlink()
                return None
                
            return data['value']
        except (json.JSONDecodeError, KeyError):
            return None
    
    def _set_file(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in file."""
        file_path = Path(self.cache_dir) / f"{key}.cache"
        expire_at = time.time() + ttl if ttl else None
        
        data = {
            'value': value,
            'expire_at': expire_at
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f)
    
    def _delete_file(self, key: str) -> None:
        """Delete value from file."""
        file_path = Path(self.cache_dir) / f"{key}.cache"
        if file_path.exists():
            file_path.unlink()

def cache(ttl: Optional[int] = None):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Cache lifetime in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Get value from cache
            cached_value = await wrapper.cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await wrapper.cache.set(cache_key, result, ttl)
            return result
        
        # Create cache instance for function
        wrapper.cache = Cache()
        return wrapper
    return decorator 