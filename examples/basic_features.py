"""
Basic features example.

Demonstrates:
- Routes with different HTTP methods
- Path and query parameters
- Request body parsing
- Response types
"""

from qakeapi import QakeAPI, Request, JSONResponse, HTMLResponse


app = QakeAPI(title="Basic Features Example")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to QakeAPI!"}


@app.get("/items/{item_id}")
async def get_item(item_id: int, q: str = None):
    """
    Get item by ID.
    
    Args:
        item_id: Item ID (path parameter)
        q: Optional query parameter
    """
    return {
        "item_id": item_id,
        "query": q,
    }


@app.post("/items")
async def create_item(request: Request):
    """Create new item."""
    data = await request.json()
    return JSONResponse(
        {"created": data},
        status_code=201,
    )


@app.put("/items/{item_id}")
async def update_item(item_id: int, request: Request):
    """Update item."""
    data = await request.json()
    return {
        "item_id": item_id,
        "updated": data,
    }


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete item."""
    return {"deleted": item_id}


@app.get("/html")
async def html_example():
    """Return HTML response."""
    return HTMLResponse("<h1>Hello, World!</h1>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

