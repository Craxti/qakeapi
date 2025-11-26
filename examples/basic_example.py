"""
Basic QakeAPI 1.2.0 Example.

This example demonstrates the revolutionary features of QakeAPI:
- Hybrid sync/async support
- Smart routing
- Reactive events
- Parallel dependencies
"""

from qakeapi import QakeAPI, CORSMiddleware

app = QakeAPI(
    title="QakeAPI 1.2.0 Example",
    version="1.2.0",
    description="Example demonstrating QakeAPI features",
    debug=True,
)

# Add CORS middleware for Swagger UI
app.add_middleware(CORSMiddleware(allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]))


# Example 1: Sync function - automatically converted to async!
@app.get("/users/{id}")
def get_user(id: int):
    """Get user by ID - sync function works automatically!"""
    # This sync function is automatically executed in thread pool
    return {"id": id, "name": f"User {id}", "type": "sync"}


# Example 2: Async function - works normally
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Get item by ID - async function."""
    return {"item_id": item_id, "name": f"Item {item_id}", "type": "async"}


# Example 3: Query parameters
@app.get("/search")
def search(q: str, limit: int = 10):
    """Search endpoint with query parameters."""
    return {
        "query": q,
        "limit": limit,
        "results": [f"Result {i} for {q}" for i in range(limit)],
    }


# Example 4: Reactive events
@app.react("user:created")
async def on_user_created(event):
    """React to user creation event."""
    print(f"User created: {event.data}")
    # Here you can send email, create profile, etc.


@app.post("/users")
async def create_user(request):
    """Create user and emit event."""
    data = await request.json()
    user_id = data.get("id", 1)
    
    # Emit event - all reactors will be called
    await app.emit("user:created", {"id": user_id, "name": data.get("name")})
    
    return {"message": "User created", "user_id": user_id}


# Example 5: Conditional routing
@app.when(lambda req: req.headers.get("x-client") == "mobile")
def mobile_handler(request):
    """Handler for mobile clients."""
    return {"client": "mobile", "message": "Mobile API response"}


@app.when(lambda req: req.path.startswith("/api/v2"))
def v2_handler(request):
    """Handler for v2 API."""
    return {"version": "2.0", "path": request.path}


# Example 6: Lifecycle events
@app.on_startup
def startup():
    """Run on application startup."""
    print("QakeAPI 1.2.0 started!")


@app.on_shutdown
def shutdown():
    """Run on application shutdown."""
    print("QakeAPI 1.2.0 shutting down...")


if __name__ == "__main__":
    import uvicorn
    import sys
    import io
    
    # Fix encoding for Windows console
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 60)
    print("QakeAPI 1.2.0 - Revolutionary Web Framework")
    print("=" * 60)
    print("\nAvailable endpoints:")
    print("  GET  /users/{id}          - Get user (sync)")
    print("  GET  /items/{item_id}     - Get item (async)")
    print("  GET  /search?q=...        - Search")
    print("  POST /users               - Create user (emits event)")
    print("\nConditional routes:")
    print("  Mobile client (X-Client: mobile)")
    print("  API v2 (/api/v2/*)")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

