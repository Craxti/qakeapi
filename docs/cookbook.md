# QakeAPI Cookbook

Typical scenarios and recipes for common tasks.

---

## 1. REST API with SQLite

**Scenario:** Simple CRUD API with SQLite database.

```python
import sqlite3
from qakeapi import QakeAPI, Depends

app = QakeAPI(title="My API", version="1.0")

def get_db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@app.get("/items")
def list_items(db=Depends(get_db)):
    rows = db.execute("SELECT * FROM items").fetchall()
    return {"items": [dict(r) for r in rows]}

@app.post("/items")
async def create_item(request, db=Depends(get_db)):
    data = await request.json()
    db.execute("INSERT INTO items (name) VALUES (?)", (data["name"],))
    db.commit()
    return {"message": "Created"}
```

**See:** [examples/jwt_sqlite_example.py](../examples/jwt_sqlite_example.py)

---

## 2. JWT Authentication

**Scenario:** Protect routes with JWT tokens.

```python
from qakeapi import QakeAPI, init_auth, require_auth, create_token

app = QakeAPI(title="API", version="1.0")
init_auth(secret_key="your-secret-key", jwt_expiration=3600)

@app.post("/login")
async def login(request):
    data = await request.json()
    # Verify credentials...
    token = create_token({"user_id": 1, "username": "admin"})
    return {"token": token}

@app.get("/protected")
@require_auth()
def protected(request, user: dict):
    return {"user": user}
```

**Header:** `Authorization: Bearer <token>`

**See:** [examples/auth_example.py](../examples/auth_example.py), [examples/jwt_sqlite_example.py](../examples/jwt_sqlite_example.py)

---

## 3. Redis Caching

**Scenario:** Cache responses in Redis.

```python
import os
from qakeapi import QakeAPI, Depends

app = QakeAPI(title="API", version="1.0")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

def get_redis():
    import redis.asyncio as redis
    return redis.from_url(REDIS_URL)

@app.get("/cached")
async def cached(request, redis=Depends(get_redis)):
    key = "cache:" + (request.get_query_param("key") or "default")
    cached = await redis.get(key)
    if cached:
        return {"cached": True, "value": cached.decode()}
    value = "computed"
    await redis.setex(key, 60, value)
    return {"cached": False, "value": value}
```

**See:** [examples/redis_example.py](../examples/redis_example.py)

---

## 4. File Upload with Validation

**Scenario:** Accept file uploads with type and size limits.

```python
from qakeapi import QakeAPI, FileUpload, IMAGE_TYPES

app = QakeAPI(title="API", version="1.0")

@app.post("/upload")
async def upload(file: FileUpload):
    if not file.validate_type(IMAGE_TYPES):
        return {"error": "Only images"}, 400
    if not file.validate_size(5 * 1024 * 1024):  # 5MB
        return {"error": "File too large"}, 400
    path = await file.save("uploads/")
    return {"path": path}
```

**See:** [examples/file_upload_example.py](../examples/file_upload_example.py)

---

## 5. Rate Limiting

**Scenario:** Limit requests per minute per IP.

```python
from qakeapi import QakeAPI, rate_limit

app = QakeAPI(title="API", version="1.0")

@rate_limit(requests_per_minute=60)
@app.get("/api/data")
def get_data():
    return {"data": "..."}
```

**See:** [examples/rate_limit_example.py](../examples/rate_limit_example.py)

---

## 6. Background Tasks

**Scenario:** Send email or process data after response.

```python
from qakeapi.core.background import add_background_task

@app.post("/order")
async def create_order(request):
    data = await request.json()
    await add_background_task(send_confirmation_email, data["email"])
    return {"status": "created"}
```

**See:** [docs/background-tasks.md](background-tasks.md)

---

## 7. Docker Deployment

**Scenario:** Run QakeAPI in Docker with Redis.

```bash
# Build and run
docker-compose up -d

# API: http://localhost:8000
# Redis: localhost:6379
```

**Files:** [Dockerfile](../Dockerfile), [docker-compose.yml](../docker-compose.yml)

---

## 8. Pagination

**Scenario:** Paginate list results.

```python
@app.get("/items")
def list_items(limit: int = 10, offset: int = 0):
    items = get_items_from_db(limit=limit, offset=offset)
    total = get_total_count()
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
```

---

## 9. Error Handling

**Scenario:** Return custom error responses.

```python
from qakeapi.core.exceptions import HTTPException

@app.get("/items/{id}")
def get_item(id: int):
    item = find_item(id)
    if not item:
        raise HTTPException(404, "Item not found")
    return item
```

---

## 10. CORS for Frontend

**Scenario:** Allow frontend (React, Vue) to call API.

```python
from qakeapi import QakeAPI, CORSMiddleware

app = QakeAPI(title="API", version="1.0")
app.add_middleware(CORSMiddleware(
    allow_origins=["http://localhost:3000", "https://myapp.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
))
```

---

## See Also

- [Getting Started](getting-started.md)
- [Ecosystem & Integrations](ecosystem.md)
- [Examples](../examples/)
