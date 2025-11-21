"""
QakeAPI Caching Example

This example demonstrates how to use built-in caching with in-memory and Redis backends.
"""

from qakeapi import QakeAPI, Request
from qakeapi.caching.cache import CacheManager, InMemoryCache
from qakeapi.caching.middleware import CacheMiddleware

app = QakeAPI(
    title="Caching Example",
    description="Example of using caching in QakeAPI",
    version="1.0.0",
)

# Create cache instance
cache = InMemoryCache(max_size=100)

# Create cache manager
cache_manager = CacheManager(backend=cache)

# Add caching middleware
app.add_middleware(
    CacheMiddleware(
        cache_manager=cache_manager,
        cache_methods={"GET"},
        default_expire=300,  # 5 minutes
        skip_paths={"/health", "/metrics"},
    )
)


# Simulated database
fake_db = {
    1: {"id": 1, "name": "Item 1", "price": 10.99},
    2: {"id": 2, "name": "Item 2", "price": 20.99},
    3: {"id": 3, "name": "Item 3", "price": 30.99},
}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Caching Example API"}


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """
    Get item by ID (cached)

    This endpoint is automatically cached by the CacheMiddleware.
    """
    if item_id not in fake_db:
        from qakeapi.core.exceptions import HTTPException
        from qakeapi.utils.status import status

        raise HTTPException(status.NOT_FOUND, "Item not found")

    return fake_db[item_id]


@app.get("/items/")
async def get_all_items():
    """
    Get all items (cached)

    This endpoint is automatically cached.
    """
    return {"items": list(fake_db.values())}


@app.post("/items/")
async def create_item(request: Request):
    """
    Create new item (invalidates cache)

    POST requests are not cached, so cache is automatically invalidated.
    """
    data = await request.json()
    new_id = max(fake_db.keys()) + 1 if fake_db else 1
    fake_db[new_id] = {"id": new_id, **data}

    # Manually invalidate cache for items list
    await cache_manager.delete("GET:/items/")

    return fake_db[new_id]


@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics"""
    stats = cache_manager.get_stats()
    return {
        "hits": stats.get("hits", 0),
        "misses": stats.get("misses", 0),
        "size": stats.get("size", 0),
        "hit_rate": stats.get("hit_rate", 0.0),
    }


@app.delete("/cache/clear")
async def clear_cache():
    """Clear all cache"""
    cache_manager.clear()
    return {"message": "Cache cleared"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
