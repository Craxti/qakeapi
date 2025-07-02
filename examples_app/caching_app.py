# -*- coding: utf-8 -*-
"""
Caching example with QakeAPI.
"""
import sys
import os
import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import Field

# Initialize application
app = Application(
    title="Caching Example",
    version="1.0.3",
    description="Caching functionality example with QakeAPI"
)

# Pydantic models
class CacheRequest(RequestModel):
    """Cache request model"""
    key: str = Field(..., description="Cache key")
    value: str = Field(..., description="Value to cache")
    ttl: Optional[int] = Field(300, description="Time to live in seconds")

# In-memory cache storage
cache = {}
cache_stats = {
    "hits": 0,
    "misses": 0,
    "sets": 0,
    "deletes": 0
}

def generate_cache_key(data: str) -> str:
    """Generate cache key from data"""
    return hashlib.md5(data.encode()).hexdigest()

def is_cache_valid(cache_entry: Dict) -> bool:
    """Check if cache entry is still valid"""
    if "expires_at" not in cache_entry:
        return True
    
    return datetime.utcnow() < cache_entry["expires_at"]

def get_cache(key: str) -> Optional[Any]:
    """Get value from cache"""
    if key not in cache:
        cache_stats["misses"] += 1
        return None
    
    cache_entry = cache[key]
    
    if not is_cache_valid(cache_entry):
        # Remove expired entry
        del cache[key]
        cache_stats["misses"] += 1
        return None
    
    cache_stats["hits"] += 1
    return cache_entry["value"]

def set_cache(key: str, value: Any, ttl: int = 300) -> None:
    """Set value in cache"""
    expires_at = datetime.utcnow() + timedelta(seconds=ttl)
    
    cache[key] = {
        "value": value,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
        "ttl": ttl
    }
    
    cache_stats["sets"] += 1

def delete_cache(key: str) -> bool:
    """Delete value from cache"""
    if key in cache:
        del cache[key]
        cache_stats["deletes"] += 1
        return True
    return False

def clear_expired_cache() -> int:
    """Clear expired cache entries"""
    expired_keys = []
    for key, entry in cache.items():
        if not is_cache_valid(entry):
            expired_keys.append(key)
    
    for key in expired_keys:
        del cache[key]
    
    return len(expired_keys)

def fibonacci(n: int) -> int:
    """Calculate Fibonacci number (expensive computation)"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def factorial(n: int) -> int:
    """Calculate factorial (expensive computation)"""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "Caching API is running",
        "cache_stats": cache_stats,
        "cache_size": len(cache),
        "endpoints": {
            "/compute/{n}": "GET - Compute Fibonacci with caching",
            "/factorial/{n}": "GET - Compute factorial with caching",
            "/cache": "GET - Cache management",
            "/cache/{key}": "GET/POST/DELETE - Cache operations",
            "/stats": "GET - Cache statistics"
        }
    }

@app.get("/compute/{n}")
async def compute_fibonacci(request: Request):
    n = int(request.path_params.get("n"))
    """Compute Fibonacci number with caching"""
    if n < 0:
        return Response.json(
            {"error": "Number must be non-negative"},
            status_code=400
        )
    
    if n > 40:
        return Response.json(
            {"error": "Number too large for computation"},
            status_code=400
        )
    
    cache_key = f"fibonacci:{n}"
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return {
            "number": n,
            "result": cached_result,
            "source": "cache",
            "computation_time": 0
        }
    
    # Compute and cache
    start_time = time.time()
    result = fibonacci(n)
    computation_time = time.time() - start_time
    
    # Cache result for 5 minutes
    set_cache(cache_key, result, ttl=300)
    
    return {
        "number": n,
        "result": result,
        "source": "computation",
        "computation_time": f"{computation_time:.4f}s"
    }

@app.get("/factorial/{n}")
async def compute_factorial(request: Request):
    n = int(request.path_params.get("n"))
    """Compute factorial with caching"""
    if n < 0:
        return Response.json(
            {"error": "Number must be non-negative"},
            status_code=400
        )
    
    if n > 20:
        return Response.json(
            {"error": "Number too large for computation"},
            status_code=400
        )
    
    cache_key = f"factorial:{n}"
    
    # Try to get from cache
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return {
            "number": n,
            "result": cached_result,
            "source": "cache",
            "computation_time": 0
        }
    
    # Compute and cache
    start_time = time.time()
    result = factorial(n)
    computation_time = time.time() - start_time
    
    # Cache result for 10 minutes
    set_cache(cache_key, result, ttl=600)
    
    return {
        "number": n,
        "result": result,
        "source": "computation",
        "computation_time": f"{computation_time:.4f}s"
    }

@app.get("/cache")
async def get_cache_info(request: Request):
    """Get cache information"""
    # Clear expired entries
    expired_count = clear_expired_cache()
    
    cache_entries = []
    for key, entry in cache.items():
        cache_entries.append({
            "key": key,
            "value": str(entry["value"])[:100] + "..." if len(str(entry["value"])) > 100 else str(entry["value"]),
            "created_at": entry["created_at"].isoformat(),
            "expires_at": entry["expires_at"].isoformat(),
            "ttl": entry["ttl"]
        })
    
    return {
        "message": "Cache information",
        "total_entries": len(cache),
        "expired_cleared": expired_count,
        "entries": cache_entries,
        "stats": cache_stats
    }

@app.get("/cache/{key}")
async def get_cache_value(request: Request):
    key = request.path_params.get("key")
    """Get value from cache by key"""
    value = get_cache(key)
    
    if value is None:
        return Response.json(
            {"error": "Key not found in cache"},
            status_code=404
        )
    
    return {
        "key": key,
        "value": value,
        "source": "cache"
    }

@app.post("/cache/{key}")
@validate_request_body(CacheRequest)
async def set_cache_value(request: Request):
    key = request.path_params.get("key")
    """Set value in cache by key"""
    cache_data = request.validated_data
    
    set_cache(key, cache_data.value, cache_data.ttl)
    
    return {
        "message": "Value cached successfully",
        "key": key,
        "ttl": cache_data.ttl
    }

@app.delete("/cache/{key}")
async def delete_cache_value(request: Request):
    key = request.path_params.get("key")
    """Delete value from cache by key"""
    if delete_cache(key):
        return {
            "message": "Value deleted from cache",
            "key": key
        }
    else:
        return Response.json(
            {"error": "Key not found in cache"},
            status_code=404
        )
    return None

@app.get("/stats")
async def get_cache_stats(request: Request):
    """Get cache statistics"""
    # Clear expired entries
    expired_count = clear_expired_cache()
    
    hit_rate = 0
    if cache_stats["hits"] + cache_stats["misses"] > 0:
        hit_rate = cache_stats["hits"] / (cache_stats["hits"] + cache_stats["misses"])
    
    return {
        "message": "Cache statistics",
        "cache_size": len(cache),
        "expired_cleared": expired_count,
        "hit_rate": f"{hit_rate:.2%}",
        "stats": cache_stats,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/clear")
async def clear_cache(request: Request):
    """Clear all cache"""
    cache.clear()
    cache_stats["deletes"] += len(cache)
    
    return {
        "message": "Cache cleared successfully",
        "cleared_entries": len(cache)
    }

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "cache_status": "active",
        "cache_size": len(cache)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8005) 