"""
Tests for caching module.
"""

import pytest
import time
from qakeapi.caching import MemoryCache, CacheManager, CacheMiddleware


def test_memory_cache_basic():
    """Test basic memory cache operations."""
    cache = MemoryCache()
    
    # Set and get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Delete
    cache.delete("key1")
    assert cache.get("key1") is None
    
    # Clear
    cache.set("key2", "value2")
    cache.clear()
    assert cache.get("key2") is None


def test_memory_cache_ttl():
    """Test memory cache with TTL."""
    cache = MemoryCache()
    
    # Set with TTL
    cache.set("key1", "value1", ttl=1)
    assert cache.get("key1") == "value1"
    
    # Wait for expiration
    time.sleep(1.5)
    assert cache.get("key1") is None


def test_memory_cache_default_ttl():
    """Test memory cache with default TTL."""
    cache = MemoryCache(default_ttl=1)
    
    # Set without TTL (uses default)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Wait for expiration
    time.sleep(1.5)
    assert cache.get("key1") is None


def test_memory_cache_cleanup():
    """Test cache cleanup of expired entries."""
    cache = MemoryCache()
    
    # Add entries with different TTLs
    cache.set("key1", "value1", ttl=1)
    cache.set("key2", "value2", ttl=10)
    
    assert cache.size() == 2
    
    # Wait for first to expire
    time.sleep(1.5)
    
    # Cleanup
    removed = cache.cleanup_expired()
    assert removed == 1
    assert cache.size() == 1
    assert cache.get("key2") == "value2"


def test_cache_manager():
    """Test CacheManager."""
    manager = CacheManager()
    
    # Get default cache
    cache1 = manager.get_cache()
    assert cache1 is not None
    
    # Get named cache
    cache2 = manager.get_cache("custom")
    assert cache2 is not None
    assert cache2 != cache1
    
    # Same name returns same cache
    cache3 = manager.get_cache("custom")
    assert cache3 == cache2
