# Quick Start Guide

## Creating Your First API

```python
from qakeapi import Application
from pydantic import BaseModel

# Initialize application
app = Application()

# Define data model
class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False

# Basic route
@app.get("/")
async def root():
    return {"status": "online"}

# Path parameters
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

# Query parameters
@app.get("/search")
async def search_items(q: str, skip: int = 0, limit: int = 10):
    return {"query": q, "skip": skip, "limit": limit}

# Request body
@app.post("/items/")
async def create_item(item: Item):
    return item

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Testing Your API

Using `httpx` for testing:

```python
import httpx
import pytest
from qakeapi import Application

@pytest.mark.asyncio
async def test_root():
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "online"}
```

## Adding Middleware

```python
from qakeapi.middleware import Middleware
from qakeapi.responses import Response

@app.middleware
async def add_process_time_header(request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## Dependency Injection

```python
from qakeapi import Depends
from typing import Annotated

async def get_db():
    db = Database()
    try:
        yield db
    finally:
        await db.close()

@app.get("/users/")
async def read_users(db: Annotated[Database, Depends(get_db)]):
    return await db.fetch_all("SELECT * FROM users")
```

## Error Handling

```python
from qakeapi.exceptions import HTTPException

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return Response(
        content={"detail": exc.detail},
        status_code=exc.status_code
    )

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id < 0:
        raise HTTPException(
            status_code=400,
            detail="Item ID cannot be negative"
        )
    return {"item_id": item_id}
```

## Background Tasks

```python
from qakeapi import BackgroundTask

async def send_email(email: str, message: str):
    # Email sending logic here
    pass

@app.post("/send-notification/{email}")
async def send_notification(
    email: str,
    background_tasks: BackgroundTask
):
    background_tasks.add_task(send_email, email, "Welcome!")
    return {"message": "Notification scheduled"}
```

## Using Cache

```python
from qakeapi.cache import Cache

cache = Cache()

@app.get("/expensive-calculation/{number}")
@cache(ttl=300)  # Cache for 5 minutes
async def calculate(number: int):
    # Expensive calculation here
    result = await complex_calculation(number)
    return {"result": result}
```

## Next Steps

- Check out the [Core Concepts](../guide/core-concepts.md) for deeper understanding
- Learn about [Security](../guide/security.md) best practices
- Explore [Advanced Features](../advanced/performance.md) for optimization
- See [Examples](../advanced/examples.md) for more use cases 