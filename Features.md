# Features

QakeAPI comes with a rich set of features to help you build modern APIs efficiently.

## OpenAPI/Swagger Documentation

QakeAPI automatically generates OpenAPI documentation for your API:

```python
from qakeapi import Application

app = Application(
    title="My API",
    version="1.0.0",
    description="API with automatic documentation"
)

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """
    Get an item by ID.
    
    Args:
        item_id: The ID of the item to retrieve
        
    Returns:
        dict: The item data
    """
    return {"item_id": item_id}
```

Visit `/docs` to see the interactive Swagger UI documentation.

## CORS Support

Enable Cross-Origin Resource Sharing with the built-in middleware:

```python
from qakeapi.core.middleware.cors import CORSMiddleware

app.add_middleware(CORSMiddleware(
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,
    max_age=3600
))
```

## Authentication

QakeAPI provides flexible authentication options:

### Basic Authentication

```python
from qakeapi.core.middleware.auth import AuthMiddleware
from qakeapi.core.middleware.auth.backends import BasicAuthBackend

auth_backend = BasicAuthBackend()
auth_backend.add_user("admin", "password", ["admin"])

app.add_middleware(AuthMiddleware(auth_backend=auth_backend))
```

### Custom Authentication

```python
from qakeapi.core.middleware.auth import AuthMiddleware
from qakeapi.core.middleware.auth.backends import BaseAuthBackend

class CustomAuthBackend(BaseAuthBackend):
    async def authenticate(self, request):
        token = request.headers.get("Authorization")
        if token == "valid-token":
            return {"user": "admin", "roles": ["admin"]}
        return None

app.add_middleware(AuthMiddleware(auth_backend=CustomAuthBackend()))
```

## Type Hints and Validation

QakeAPI uses Python type hints and Pydantic for request/response validation:

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: Optional[str] = None

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    return item
```

## Middleware System

Create custom middleware to add functionality:

```python
from qakeapi.core.middleware import Middleware

class LoggingMiddleware(Middleware):
    async def __call__(self, request, call_next):
        print(f"Request: {request.method} {request.path}")
        response = await call_next(request)
        print(f"Response: {response.status_code}")
        return response

app.add_middleware(LoggingMiddleware())
```

## Error Handling

Comprehensive error handling with custom exceptions:

```python
from qakeapi.core.exceptions import HTTPException

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id < 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid item ID",
            headers={"X-Error": "Invalid ID"}
        )
    return {"item_id": item_id}
```

## Background Tasks

Run tasks in the background:

```python
from qakeapi.core.background import BackgroundTasks

@app.post("/items")
async def create_item(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_notification)
    return {"status": "created"}

async def send_notification():
    # Send notification logic
    pass
```

## WebSocket Support

Handle WebSocket connections:

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

## Next Steps

- Check out [Examples](Examples)
- Read [Best Practices](Best-Practices)
- Learn about [Deployment](Deployment) 