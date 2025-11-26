"""
Example demonstrating caching in QakeAPI.

This example shows how to use the @cache decorator
to cache responses and improve performance.
"""

import sys
import io
import time
from qakeapi import QakeAPI, CORSMiddleware, cache

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = QakeAPI(
    title="Caching Example API",
    version="1.0.0",
    description="Example demonstrating response caching",
    debug=True,
)

# Add CORS middleware
app.add_middleware(CORSMiddleware(allow_origins=["*"]))


# Simulate slow database query
def slow_database_query(user_id: int):
    """Simulate slow database query."""
    time.sleep(1)  # Simulate 1 second query
    return {
        "user_id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "timestamp": time.time()
    }


# Example 1: Basic caching (5 minutes TTL)
@cache(ttl=300)
@app.get("/users/{user_id}")
def get_user(user_id: int):
    """
    Get user by ID with caching.
    
    First request will be slow (1 second), subsequent requests
    within 5 minutes will be instant from cache.
    """
    print(f"⚠️  Slow database query for user {user_id}...")
    data = slow_database_query(user_id)
    return data


# Example 2: Short cache TTL (30 seconds)
@cache(ttl=30)
@app.get("/stats")
def get_stats():
    """
    Get statistics with short cache.
    
    Cached for 30 seconds - good for frequently updated data.
    """
    print("⚠️  Generating stats...")
    return {
        "total_users": 1000,
        "active_users": 750,
        "timestamp": time.time()
    }


# Example 3: Long cache TTL (1 hour) for static data
@cache(ttl=3600)
@app.get("/config")
def get_config():
    """
    Get configuration with long cache.
    
    Cached for 1 hour - good for rarely changing data.
    """
    print("⚠️  Loading config...")
    return {
        "app_name": "MyApp",
        "version": "1.0.0",
        "features": ["feature1", "feature2"]
    }


# Example 4: Cache with query parameters
@cache(ttl=60)
@app.get("/search")
def search(q: str = ""):
    """
    Search endpoint with caching.
    
    Different query parameters create different cache entries.
    """
    print(f"⚠️  Searching for: {q}")
    return {
        "query": q,
        "results": [f"Result 1 for {q}", f"Result 2 for {q}"],
        "count": 2
    }


# Example 5: No caching (always fresh)
@app.get("/time")
def get_time():
    """
    Get current time - no caching.
    
    Always returns fresh data.
    """
    return {
        "time": time.time(),
        "formatted": time.strftime("%Y-%m-%d %H:%M:%S")
    }


# Example 6: Custom cache key
@cache(
    ttl=120,
    key_func=lambda req: f"user:{req.get_query_param('user_id')}:data"
)
@app.get("/user-data")
def get_user_data(request):
    """
    User-specific data with custom cache key.
    
    Cache key includes user ID from query parameter.
    """
    user_id = request.get_query_param("user_id", "unknown")
    print(f"⚠️  Loading data for user {user_id}...")
    return {
        "user_id": user_id,
        "data": f"Data for user {user_id}",
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("QakeAPI Caching Example")
    print("=" * 60)
    print("\nEndpoints:")
    print("  GET  /users/{user_id}  - Cached 5 minutes (slow first time)")
    print("  GET  /stats            - Cached 30 seconds")
    print("  GET  /config           - Cached 1 hour")
    print("  GET  /search?q=...     - Cached 1 minute (per query)")
    print("  GET  /time             - No cache (always fresh)")
    print("  GET  /user-data?user_id=... - Custom cache key")
    print("\nTry these requests:")
    print("  # First request - slow (from database)")
    print("  curl http://localhost:8000/users/1")
    print("\n  # Second request - instant (from cache)")
    print("  curl http://localhost:8000/users/1")
    print("\n  # Check cache headers")
    print("  curl -v http://localhost:8000/users/1")
    print("\nSwagger UI: http://localhost:8000/docs")
    print("OpenAPI spec is also cached for 1 hour")
    print("=" * 60)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

