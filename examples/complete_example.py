"""
Complete QakeAPI 1.2.0 example with all features.

Demonstrates:
- Hybrid sync/async support
- Automatic parameter extraction from body
- Middleware system
- WebSocket support
- Background tasks
- Reactive events
- OpenAPI documentation (/docs and /openapi.json)
"""

from qakeapi import (
    QakeAPI,
    Request,
    WebSocket,
    CORSMiddleware,
    LoggingMiddleware,
    add_background_task,
)

app = QakeAPI(
    title="QakeAPI 1.2.0 Complete Example",
    version="1.2.0",
    description="Complete example demonstrating all QakeAPI features",
    debug=True,
)

# Middleware
app.add_middleware(LoggingMiddleware())
app.add_middleware(CORSMiddleware(allow_origins=["*"]))


# Example 1: Sync function (works automatically!)
@app.get("/users/{id}")
def get_user(id: int):
    """Get user by ID - sync function!"""
    return {"id": id, "name": f"User {id}", "type": "sync"}


# Example 2: Async function
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Get item by ID - async function."""
    return {"item_id": item_id, "name": f"Item {item_id}", "type": "async"}


# Example 3: POST with automatic body extraction
class UserCreate:
    """Model for creating user."""
    
    def __init__(self, name: str, email: str, age: int = None):
        self.name = name
        self.email = email
        self.age = age
    
    def dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "age": self.age,
        }


@app.post("/users")
async def create_user(user: UserCreate):
    """
    Create user - automatic body extraction!
    
    Body will be automatically extracted and converted to UserCreate.
    """
    # Send task to background
    await add_background_task(send_welcome_email, user.email)
    
    # Emit event
    await app.emit("user:created", user.dict())
    
    return {
        "message": "User created",
        "user": user.dict(),
    }


# Example 4: Background task
async def send_welcome_email(email: str):
    """Send welcome email - background task."""
    import asyncio
    
    print(f"[Background] Sending welcome email to {email}")
    # Here you can use real email sending logic
    await asyncio.sleep(1)  # Simulate sending
    print(f"[Background] Email sent to {email}")


# Example 5: Reactive event
@app.react("user:created")
async def on_user_created(event):
    """React to user creation event."""
    print(f"[Event] User created: {event.data}")
    # Here you can create profile, send notifications, etc.


# Example 6: WebSocket
@app.websocket("/ws/{room}")
async def websocket_handler(websocket: WebSocket, room: str):
    """WebSocket handler."""
    await websocket.accept()
    await websocket.send_json({"message": f"Welcome to room {room}!"})
    
    async for message in websocket.iter_json():
        await websocket.send_json({
            "echo": message,
            "room": room,
        })


# Example 7: Query parameters
@app.get("/search")
def search(q: str, limit: int = 10):
    """Search with query parameters."""
    return {
        "query": q,
        "limit": limit,
        "results": [f"Result {i} for {q}" for i in range(limit)],
    }


# Example 8: Lifecycle events
@app.on_startup
def startup():
    """Run on application startup."""
    print("QakeAPI 1.2.0 Application started!")


@app.on_shutdown
def shutdown():
    """Run on application shutdown."""
    print("QakeAPI 1.2.0 Application shutting down...")


if __name__ == "__main__":
    import asyncio
    import uvicorn
    import sys
    import io
    
    # Fix encoding for Windows console
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 60)
    print("QakeAPI 1.2.0 - Complete Example")
    print("=" * 60)
    print("\nFeatures demonstrated:")
    print("  Hybrid sync/async support")
    print("  Automatic body parameter extraction")
    print("  Middleware system (Logging, CORS)")
    print("  WebSocket support")
    print("  Background tasks")
    print("  Reactive events")
    print("  OpenAPI documentation")
    print("\nAvailable endpoints:")
    print("  GET  /users/{id}          - Get user (sync)")
    print("  GET  /items/{item_id}     - Get item (async)")
    print("  POST /users               - Create user (auto body extraction)")
    print("  GET  /search?q=...        - Search")
    print("  WS   /ws/{room}           - WebSocket connection")
    print("\nDocumentation:")
    print("  http://localhost:8000/docs        - Swagger UI")
    print("  http://localhost:8000/openapi.json - OpenAPI spec")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
