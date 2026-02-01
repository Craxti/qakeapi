# Migration Guide: FastAPI to QakeAPI

This guide helps you migrate an existing FastAPI application to QakeAPI. Both frameworks share similar concepts, which makes migration straightforward.

## Why Migrate to QakeAPI?

| Benefit | Impact |
|---------|--------|
| **Zero dependencies** | No Pydantic, Starlette — smaller install, fewer security updates, ~15–25% less overhead per request |
| **Faster routing** | Trie-based lookup: O(path length) vs O(routes). 100 routes → ~1.2μs vs ~2.8μs (FastAPI) |
| **Built-in caching** | `@cache(ttl=300)` — no Redis for simple cases. Cache hits ~42K RPS |
| **Built-in rate limiting** | `@rate_limit(60)` — no slowapi or custom middleware |
| **Parallel dependencies** | Same `Depends` pattern, but lighter; 3 deps → 2.8x faster than sequential |
| **Reactive events** | `emit`/`react` in core — no Celery for simple event-driven flows |
| **Same DX** | Decorators, OpenAPI, WebSocket — familiar if you know FastAPI |

See [benchmarks](benchmarks.md) for detailed numbers.

## Key Differences

| Aspect | FastAPI | QakeAPI |
|--------|---------|---------|
| Dependencies | Pydantic, Starlette, Uvicorn | Zero (core), optional Uvicorn |
| Sync/Async | Async-first, sync in threadpool | Hybrid: both natively supported |
| Validation | Pydantic models | Built-in validation, type hints |
| DI | `Depends()` | `Depends()` (same pattern) |
| OpenAPI | Automatic | Automatic |
| WebSocket | Supported | Supported |

## Step-by-Step Migration

### 1. Installation

**FastAPI:**
```bash
pip install fastapi uvicorn
```

**QakeAPI:**
```bash
pip install qakeapi
pip install uvicorn  # optional, for running server
```

### 2. Application Setup

**FastAPI:**
```python
from fastapi import FastAPI

app = FastAPI(
    title="My API",
    version="1.0.0",
    description="My API description"
)
```

**QakeAPI:**
```python
from qakeapi import QakeAPI

app = QakeAPI(
    title="My API",
    version="1.0.0",
    description="My API description"
)
```

### 3. Route Handlers

**FastAPI (async):**
```python
@app.get("/users/{id}")
async def get_user(id: int):
    return {"id": id, "name": f"User {id}"}
```

**QakeAPI (same):**
```python
@app.get("/users/{id}")
async def get_user(id: int):
    return {"id": id, "name": f"User {id}"}
```

**FastAPI (sync - runs in threadpool):**
```python
@app.get("/users/{id}")
def get_user(id: int):
    return {"id": id, "name": f"User {id}"}
```

**QakeAPI (sync - automatic conversion):**
```python
@app.get("/users/{id}")
def get_user(id: int):
    return {"id": id, "name": f"User {id}"}
```

### 4. Request Body

**FastAPI:**
```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str

@app.post("/users")
async def create_user(user: UserCreate):
    return {"message": "User created", "data": user.dict()}
```

**QakeAPI:**
```python
@app.post("/users")
async def create_user(request):
    data = await request.json()
    # Validate manually or use validate_request_body
    return {"message": "User created", "data": data}
```

Or with validation:
```python
from qakeapi import validate_request_body

@app.post("/users")
async def create_user(request):
    data = await validate_request_body(request, {"name": str, "email": str})
    return {"message": "User created", "data": data}
```

### 5. Dependency Injection

**FastAPI:**
```python
from fastapi import Depends

def get_db():
    return Database()

@app.get("/users")
async def get_users(db = Depends(get_db)):
    return await db.get_users()
```

**QakeAPI (same pattern):**
```python
from qakeapi import Depends

def get_db():
    return Database()

@app.get("/users")
async def get_users(db = Depends(get_db)):
    return await db.get_users()
```

### 6. CORS

**FastAPI:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**QakeAPI:**
```python
from qakeapi import CORSMiddleware

app.add_middleware(CORSMiddleware(allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]))
```

### 7. Background Tasks

**FastAPI:**
```python
from fastapi import BackgroundTasks

@app.post("/process")
async def process(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, "user@example.com")
    return {"message": "Processing"}
```

**QakeAPI:**
```python
from qakeapi.core.background import add_background_task

@app.post("/process")
async def process():
    await add_background_task(send_email, "user@example.com")
    return {"message": "Processing"}
```

### 8. WebSocket

**FastAPI:**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

**QakeAPI:**
```python
from qakeapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    async for message in websocket.iter_text():
        await websocket.send_text(f"Echo: {message}")
```

### 9. Running the Server

Both use Uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or in code:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Migration Checklist

- [ ] Replace `FastAPI` with `QakeAPI`
- [ ] Replace `from fastapi import ...` with `from qakeapi import ...`
- [ ] Convert Pydantic models to dict validation or dataclasses
- [ ] Update background tasks to use `add_background_task`
- [ ] Update WebSocket handlers if needed
- [ ] Test all endpoints
- [ ] Verify OpenAPI docs at `/docs`
- [ ] Update deployment configuration if needed

## When to Choose QakeAPI

- You want **zero dependencies** in core
- You need **hybrid sync/async** without explicit threadpool handling
- You're migrating from Flask and want async support
- You prefer minimal external dependencies for security/audit
- You want **reactive events** and **pipeline composition** built-in

## Need Help?

- [Documentation](getting-started.md)
- [API Reference](api-reference.md)
- [GitHub Issues](https://github.com/craxti/qakeapi/issues)
