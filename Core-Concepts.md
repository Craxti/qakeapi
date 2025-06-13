# Core Concepts

This page explains the fundamental concepts and components of QakeAPI.

## Application

The `Application` class is the main entry point for your QakeAPI application. It handles routing, middleware, and request processing.

```python
from qakeapi import Application

app = Application(
    title="My API",
    version="1.0.0",
    description="A sample API built with QakeAPI"
)
```

## Routing

QakeAPI provides decorators for defining routes with different HTTP methods:

```python
@app.get("/items")
async def get_items():
    return {"items": []}

@app.post("/items")
async def create_item():
    return {"status": "created"}

@app.put("/items/{item_id}")
async def update_item(item_id: int):
    return {"item_id": item_id}

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    return {"status": "deleted"}
```

## Request/Response

### Request

The request object provides access to:
- Headers
- Query parameters
- Path parameters
- Request body
- Cookies
- Client information

```python
@app.post("/items")
async def create_item(request):
    data = await request.json()
    headers = request.headers
    return {"data": data}
```

### Response

The `Response` class helps create HTTP responses:

```python
from qakeapi.core.responses import Response

@app.get("/")
async def home():
    return Response.json(
        {"message": "Hello"},
        status_code=200,
        headers=[(b"X-Custom", b"value")]
    )
```

## Middleware

Middleware functions can modify requests and responses. They are executed in the order they are added:

```python
from qakeapi.core.middleware import Middleware

async def logging_middleware(request, call_next):
    print(f"Request: {request.method} {request.path}")
    response = await call_next(request)
    print(f"Response: {response.status_code}")
    return response

app.add_middleware(logging_middleware)
```

### Built-in Middleware

1. **CORS Middleware**:
```python
from qakeapi.core.middleware.cors import CORSMiddleware

app.add_middleware(CORSMiddleware(
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
))
```

2. **Authentication Middleware**:
```python
from qakeapi.core.middleware.auth import AuthMiddleware

app.add_middleware(AuthMiddleware(
    auth_backend=BasicAuthBackend()
))
```

## Error Handling

QakeAPI provides built-in error handling:

```python
from qakeapi.core.exceptions import HTTPException

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id < 0:
        raise HTTPException(status_code=400, detail="Invalid item ID")
    return {"item_id": item_id}
```

## Type Hints

QakeAPI uses Python type hints for:
- Request validation
- Response serialization
- OpenAPI documentation

```python
from typing import List
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

@app.get("/items", response_model=List[Item])
async def get_items():
    return [
        {"name": "Item 1", "price": 10.0},
        {"name": "Item 2", "price": 20.0}
    ]
```

## Next Steps

- Learn about [Features](Features)
- Check out [Examples](Examples)
- Read [Best Practices](Best-Practices) 