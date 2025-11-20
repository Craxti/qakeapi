"""
Basic QakeAPI Usage Example

This example demonstrates basic features of QakeAPI:
- Simple routes (GET, POST, PUT, DELETE)
- Path parameters
- Query parameters
- Lifecycle events
"""
from qakeapi import QakeAPI, Request, JSONResponse
from qakeapi.middleware.cors import CORSMiddleware
from qakeapi.middleware.logging import LoggingMiddleware

# Create application
app = QakeAPI(
    title="Basic QakeAPI Application",
    description="Example of a simple web application using QakeAPI",
    version="1.0.0",
    debug=True,
)

# Add middleware
app.add_middleware(CORSMiddleware(
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
))
app.add_middleware(LoggingMiddleware())


# Simple routes
@app.get("/")
async def root():
    """Home page"""
    return {"message": "Welcome to QakeAPI!"}


@app.get("/hello/{name}")
async def hello(name: str):
    """Greeting with name"""
    return {"message": f"Hello, {name}!"}


@app.get("/items/{item_id}")
async def get_item(item_id: int, q: str = None):
    """Get item by ID"""
    return {"item_id": item_id, "q": q}


@app.post("/items/")
async def create_item(request: Request):
    """Create new item"""
    data = await request.json()
    return {"message": "Item created", "data": data}


@app.put("/items/{item_id}")
async def update_item(item_id: int, request: Request):
    """Update item"""
    data = await request.json()
    return {"message": f"Item {item_id} updated", "data": data}


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete item"""
    return {"message": f"Item {item_id} deleted"}


# Lifecycle events
@app.on_event("startup")
async def startup():
    print("🚀 Application starting...")


@app.on_event("shutdown")
async def shutdown():
    print("🛑 Application shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
