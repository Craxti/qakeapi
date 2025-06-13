# Examples

This page provides practical examples of using QakeAPI for different use cases.

## Basic API

A simple REST API with CRUD operations:

```python
from qakeapi import Application
from qakeapi.core.responses import Response
from pydantic import BaseModel
from typing import List, Optional

app = Application(title="Items API")

class Item(BaseModel):
    id: Optional[int] = None
    name: str
    price: float
    description: Optional[str] = None

items = []

@app.get("/items", response_model=List[Item])
async def get_items():
    return items

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    item.id = len(items) + 1
    items.append(item)
    return item

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    for item in items:
        if item.id == item_id:
            return item
    return Response.json(
        {"error": "Item not found"},
        status_code=404
    )

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item):
    for i, stored_item in enumerate(items):
        if stored_item.id == item_id:
            item.id = item_id
            items[i] = item
            return item
    return Response.json(
        {"error": "Item not found"},
        status_code=404
    )

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(items):
        if item.id == item_id:
            items.pop(i)
            return {"status": "deleted"}
    return Response.json(
        {"error": "Item not found"},
        status_code=404
    )
```

## CORS Application

An API with CORS support for cross-origin requests:

```python
from qakeapi import Application
from qakeapi.core.middleware.cors import CORSMiddleware

app = Application(title="CORS API")

# Add CORS middleware
app.add_middleware(CORSMiddleware(
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True
))

@app.get("/api/data")
async def get_data():
    return {"message": "This endpoint is CORS-enabled"}
```

## Authentication

An API with authentication and role-based access control:

```python
from qakeapi import Application
from qakeapi.core.middleware.auth import AuthMiddleware
from qakeapi.core.middleware.auth.backends import BasicAuthBackend
from qakeapi.core.middleware.auth.decorators import requires_auth, requires_role

app = Application(title="Auth API")

# Setup authentication
auth_backend = BasicAuthBackend()
auth_backend.add_user("admin", "admin123", ["admin"])
auth_backend.add_user("user", "user123", ["user"])

app.add_middleware(AuthMiddleware(auth_backend=auth_backend))

@app.get("/public")
async def public_endpoint():
    return {"message": "This endpoint is public"}

@app.get("/protected")
@requires_auth()
async def protected_endpoint(request):
    return {
        "message": "This endpoint requires authentication",
        "user": request.user
    }

@app.get("/admin")
@requires_role("admin")
async def admin_endpoint(request):
    return {
        "message": "This endpoint requires admin role",
        "user": request.user
    }
```

## Custom Middleware

An example of creating and using custom middleware:

```python
from qakeapi import Application
from qakeapi.core.middleware import Middleware
import time

app = Application(title="Middleware API")

class TimingMiddleware(Middleware):
    async def __call__(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers.append(
            (b"X-Process-Time", str(process_time).encode())
        )
        return response

class LoggingMiddleware(Middleware):
    async def __call__(self, request, call_next):
        print(f"Request: {request.method} {request.path}")
        response = await call_next(request)
        print(f"Response: {response.status_code}")
        return response

# Add middleware in order
app.add_middleware(TimingMiddleware())
app.add_middleware(LoggingMiddleware())

@app.get("/")
async def home():
    return {"message": "Hello, World!"}
```

## WebSocket Application

A real-time chat application using WebSocket:

```python
from qakeapi import Application
from qakeapi.core.websockets import WebSocket
from typing import List

app = Application(title="Chat API")

# Store active connections
connections: List[WebSocket] = []

@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast message to all connected clients
            for connection in connections:
                await connection.send_text(f"Message: {data}")
    except:
        connections.remove(websocket)
```

## Next Steps

- Read [Best Practices](Best-Practices)
- Learn about [Deployment](Deployment)
- Check out [Contributing](Contributing) 