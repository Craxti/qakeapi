# Best Practices

This guide provides best practices and recommendations for building applications with QakeAPI.

## Project Structure

Organize your project with a clear structure:

```
my_api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── items.py
│   │   │   └── users.py
│   │   └── models/
│   │       ├── __init__.py
│   │       └── schemas.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   └── db/
│       ├── __init__.py
│       └── database.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_api/
│       ├── __init__.py
│       └── test_items.py
├── requirements.txt
└── README.md
```

## Error Handling

Implement consistent error handling:

```python
from qakeapi.core.exceptions import HTTPException
from typing import Optional

class APIError(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None
    ):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"X-Error-Code": error_code} if error_code else None
        )

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    try:
        item = await get_item_from_db(item_id)
        if not item:
            raise APIError(
                status_code=404,
                detail="Item not found",
                error_code="ITEM_NOT_FOUND"
            )
        return item
    except DatabaseError as e:
        raise APIError(
            status_code=500,
            detail="Database error",
            error_code="DB_ERROR"
        )
```

## Configuration Management

Use environment variables for configuration:

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "My API"
    debug: bool = False
    database_url: str
    secret_key: str
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()
```

## Testing

Write comprehensive tests:

```python
import pytest
from qakeapi import Application
from qakeapi.testing import TestClient

@pytest.fixture
def app():
    return Application()

@pytest.fixture
def client(app):
    return TestClient(app)

def test_get_items(client):
    response = client.get("/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_item(client):
    response = client.post(
        "/items",
        json={"name": "Test Item", "price": 10.0}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Item"
```

## Security

Follow security best practices:

1. **Use HTTPS**:
```python
app = Application(
    title="Secure API",
    ssl_keyfile="key.pem",
    ssl_certfile="cert.pem"
)
```

2. **Implement Rate Limiting**:
```python
from qakeapi.core.middleware import Middleware
from collections import defaultdict
import time

class RateLimitMiddleware(Middleware):
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    async def __call__(self, request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < 60
        ]
        
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return Response.json(
                {"error": "Rate limit exceeded"},
                status_code=429
            )
        
        self.requests[client_ip].append(now)
        return await call_next(request)
```

## Performance

Optimize your application:

1. **Use Connection Pooling**:
```python
from databases import Database

database = Database(
    "postgresql://user:pass@localhost/db",
    min_size=5,
    max_size=20
)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
```

2. **Implement Caching**:
```python
from qakeapi.core.cache import Cache

cache = Cache()

@app.get("/items/{item_id}")
@cache.cached(ttl=300)  # Cache for 5 minutes
async def get_item(item_id: int):
    return await get_item_from_db(item_id)
```

## Documentation

Write clear documentation:

```python
@app.post("/items", response_model=Item)
async def create_item(item: Item):
    """
    Create a new item.
    
    Args:
        item: The item data
        
    Returns:
        Item: The created item
        
    Raises:
        HTTPException: If the item data is invalid
    """
    return await create_item_in_db(item)
```

## Deployment

Prepare your application for production:

1. **Use Gunicorn**:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. **Environment Variables**:
```bash
export QAKEAPI_DEBUG=false
export QAKEAPI_DATABASE_URL=postgresql://user:pass@localhost/db
export QAKEAPI_SECRET_KEY=your-secret-key
```

## Next Steps

- Learn about [Deployment](Deployment)
- Check out [Contributing](Contributing)
- Read the [FAQ](FAQ) 