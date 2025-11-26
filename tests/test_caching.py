"""
Tests for caching system.
"""

import pytest
import time
from qakeapi.core.caching import Cache, get_cache, generate_cache_key, cache


class TestCache:
    """Tests for Cache class."""
    
    def test_cache_creation(self):
        """Test creating a cache."""
        cache_instance = Cache()
        assert cache_instance._cache == {}
    
    def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        cache_instance = Cache()
        
        cache_instance.set("key1", "value1", ttl=60)
        value = cache_instance.get("key1")
        
        assert value == "value1"
    
    def test_cache_expiration(self):
        """Test cache expiration."""
        cache_instance = Cache()
        
        cache_instance.set("key1", "value1", ttl=1)
        
        # Should be available immediately
        assert cache_instance.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be None after expiration
        assert cache_instance.get("key1") is None
    
    def test_cache_delete(self):
        """Test deleting cache entries."""
        cache_instance = Cache()
        
        cache_instance.set("key1", "value1", ttl=60)
        assert cache_instance.get("key1") == "value1"
        
        cache_instance.delete("key1")
        assert cache_instance.get("key1") is None
    
    def test_cache_clear(self):
        """Test clearing all cache entries."""
        cache_instance = Cache()
        
        cache_instance.set("key1", "value1", ttl=60)
        cache_instance.set("key2", "value2", ttl=60)
        
        assert len(cache_instance._cache) == 2
        
        cache_instance.clear()
        assert len(cache_instance._cache) == 0
    
    def test_cache_cleanup_expired(self):
        """Test cleaning up expired entries."""
        cache_instance = Cache()
        
        cache_instance.set("key1", "value1", ttl=1)
        cache_instance.set("key2", "value2", ttl=60)
        
        # Wait for key1 to expire
        time.sleep(1.1)
        
        removed = cache_instance.cleanup_expired()
        assert removed == 1
        assert cache_instance.get("key1") is None
        assert cache_instance.get("key2") == "value2"
    
    def test_cache_get_stats(self):
        """Test getting cache statistics."""
        cache_instance = Cache()
        
        cache_instance.set("key1", "value1", ttl=1)
        cache_instance.set("key2", "value2", ttl=60)
        
        stats = cache_instance.get_stats()
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 2
        assert stats["expired_entries"] == 0
        
        # Wait for key1 to expire
        time.sleep(1.1)
        
        stats = cache_instance.get_stats()
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 1
        assert stats["expired_entries"] == 1


class TestGetCache:
    """Tests for get_cache function."""
    
    def test_get_cache(self):
        """Test getting global cache instance."""
        cache_instance = get_cache()
        assert isinstance(cache_instance, Cache)
        
        # Should return same instance
        cache_instance2 = get_cache()
        assert cache_instance is cache_instance2


class TestGenerateCacheKey:
    """Tests for generate_cache_key function."""
    
    def test_generate_cache_key_basic(self):
        """Test generating basic cache key."""
        key = generate_cache_key(path="/api/users", method="GET")
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hash length
    
    def test_generate_cache_key_with_query(self):
        """Test generating cache key with query parameters."""
        key1 = generate_cache_key(
            path="/api/users",
            method="GET",
            query_params={"page": "1", "limit": "10"}
        )
        
        key2 = generate_cache_key(
            path="/api/users",
            method="GET",
            query_params={"limit": "10", "page": "1"}  # Different order
        )
        
        # Should be same (sorted)
        assert key1 == key2
    
    def test_generate_cache_key_with_headers(self):
        """Test generating cache key with headers."""
        headers = {"accept": "application/json", "authorization": "Bearer token"}
        
        key1 = generate_cache_key(
            path="/api/data",
            method="GET",
            headers=headers,
            include_headers=True
        )
        
        key2 = generate_cache_key(
            path="/api/data",
            method="GET",
            headers=headers,
            include_headers=False
        )
        
        # Should be different
        assert key1 != key2
    
    def test_generate_cache_key_different_methods(self):
        """Test that different methods generate different keys."""
        key1 = generate_cache_key(path="/api/users", method="GET")
        key2 = generate_cache_key(path="/api/users", method="POST")
        
        assert key1 != key2


class TestCacheDecorator:
    """Tests for cache decorator."""
    
    def test_cache_decorator(self):
        """Test cache decorator."""
        @cache(ttl=300)
        def handler():
            return {"data": "test"}
        
        assert hasattr(handler, "_cache_config")
        assert handler._cache_config["ttl"] == 300
        assert handler._cache_config["key_func"] is None
    
    def test_cache_with_custom_key(self):
        """Test cache decorator with custom key function."""
        def key_func(request):
            return f"custom:{request.path}"
        
        @cache(ttl=60, key_func=key_func)
        def handler():
            return {"data": "test"}
        
        assert handler._cache_config["key_func"] == key_func
        assert handler._cache_config["ttl"] == 60
    
    def test_cache_with_headers(self):
        """Test cache decorator with include_headers."""
        @cache(ttl=300, include_headers=True)
        def handler():
            return {"data": "test"}
        
        assert handler._cache_config["include_headers"] is True

