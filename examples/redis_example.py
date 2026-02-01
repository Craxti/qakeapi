"""
QakeAPI Redis Example.

Demonstrates:
- Redis for caching API responses
- Redis for session storage
- Depends(get_redis) for connection
"""

import os
from qakeapi import QakeAPI, CORSMiddleware, Depends, cache

app = QakeAPI(
    title="QakeAPI Redis Example",
    version="1.3.1",
    description="Redis caching and session storage",
    debug=True,
)
app.add_middleware(CORSMiddleware(allow_origins=["*"]))

# Redis URL - default to localhost
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


def get_redis():
    """Get Redis connection. Requires: pip install redis"""
    try:
        import redis.asyncio as redis
    except ImportError:
        raise RuntimeError("Install redis: pip install redis")
    return redis.from_url(REDIS_URL)


@app.get("/")
def root():
    """Public endpoint."""
    return {"message": "QakeAPI Redis Example", "redis_url": REDIS_URL}


@app.get("/cached-internal")
@cache(ttl=60)
def cached_internal():
    """Uses built-in in-memory cache (no Redis)."""
    return {"source": "in-memory", "cached": True}


@app.get("/cached-redis")
async def cached_redis(request, redis=Depends(get_redis)):
    """Cache in Redis. GET /cached-redis?key=foo"""
    key = "qakeapi:cache:" + (request.get_query_param("key") or "default")
    cached = await redis.get(key)
    if cached:
        return {"source": "redis", "cached": True, "value": cached.decode()}
    value = f"cached-value-{key}"
    await redis.setex(key, 60, value)
    return {"source": "redis", "cached": False, "value": value}


@app.get("/redis-stats")
async def redis_stats(redis=Depends(get_redis)):
    """Get Redis info."""
    try:
        info = await redis.info("server")
        return {
            "redis_version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
        }
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    import uvicorn
    print("Redis Example: http://127.0.0.1:8000")
    print("Docs: http://127.0.0.1:8000/docs")
    print("Requires: pip install redis, Redis server on localhost:6379")
    print("Or: docker run -p 6379:6379 redis")
    uvicorn.run(app, host="0.0.0.0", port=8000)
