"""
Basic example of QakeAPI usage.

This example demonstrates:
- Creating an application
- Defining routes
- Handling requests
- Returning JSON responses
"""

from qakeapi import JSONResponse, QakeAPI, Request

# Create application
app = QakeAPI(
    title="Basic Example API",
    version="1.1.0",
    description="A simple example API",
    debug=True,
)


# Simple GET route
@app.get("/")
async def root(request: Request):
    """Root endpoint."""
    return {"message": "Hello, World!", "path": request.path}


# Route with path parameter
@app.get("/users/{user_id}")
async def get_user(request: Request):
    """Get user by ID."""
    user_id = request.get_path_param("user_id")
    return {
        "user_id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
    }


# POST route with JSON body
@app.post("/users")
async def create_user(request: Request):
    """Create a new user."""
    data = await request.json()
    return {
        "message": "User created",
        "user": data,
        "id": 123,
    }


# Route with query parameters
@app.get("/search")
async def search(request: Request):
    """Search endpoint with query parameters."""
    query = request.get_query_param("q", "")
    limit = request.get_query_param("limit", "10")

    return {
        "query": query,
        "limit": int(limit),
        "results": [
            {"id": 1, "title": f"Result for {query}"},
            {"id": 2, "title": f"Another result for {query}"},
        ],
    }


# Lifecycle events
@app.on_event("startup")
async def startup():
    """Run on application startup."""
    print("Application starting...")


@app.on_event("shutdown")
async def shutdown():
    """Run on application shutdown."""
    print("Application shutting down...")


# Exception handler
@app.exception_handler(404)
async def not_found_handler(scope, receive, exc):
    """Custom 404 handler."""
    return JSONResponse(
        {"error": "Not Found", "path": scope.get("path")},
        status_code=404,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
