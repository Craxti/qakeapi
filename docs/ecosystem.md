# QakeAPI Ecosystem & Integrations

This document describes how to integrate QakeAPI with popular Python libraries and services.

## Database

### SQLite

```python
from qakeapi import QakeAPI, Depends
import sqlite3

app = QakeAPI()

def get_db():
    conn = sqlite3.connect("app.db")
    try:
        yield conn
    finally:
        conn.close()

@app.get("/users")
def get_users(db = Depends(get_db)):
    cursor = db.execute("SELECT * FROM users")
    return [dict(row) for row in cursor.fetchall()]
```

### SQLAlchemy (async)

```python
from qakeapi import QakeAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

app = QakeAPI()
engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/users")
async def get_users(db = Depends(get_db)):
    result = await db.execute(select(User))
    return [u.dict() for u in result.scalars()]
```

## Caching

### In-Memory (built-in)

```python
from qakeapi import cache

@cache(ttl=300)
@app.get("/expensive")
def expensive():
    return compute()
```

### Redis (custom)

```python
import redis.asyncio as redis
from qakeapi import QakeAPI, Depends

app = QakeAPI()
r = redis.from_url("redis://localhost")

def get_cache():
    return r

@app.get("/cached")
async def cached(key: str, cache = Depends(get_cache)):
    val = await cache.get(key)
    if val:
        return {"cached": val}
    return {"cached": None}
```

## HTTP Client

### httpx

```python
import httpx
from qakeapi import QakeAPI, Depends

app = QakeAPI()

async def get_client():
    async with httpx.AsyncClient() as client:
        yield client

@app.get("/proxy")
async def proxy(client = Depends(get_client)):
    r = await client.get("https://api.example.com/data")
    return r.json()
```

## Message Queues

### Background tasks (built-in)

For fire-and-forget jobs, use built-in background tasks:

```python
from qakeapi.core.background import add_background_task

@app.post("/order")
async def create_order(request):
    data = await request.json()
    await add_background_task(send_confirmation_email, data["email"])
    return {"status": "created"}
```

### Celery (for distributed queues)

```python
from celery import Celery
from qakeapi.core.background import add_background_task

celery_app = Celery("tasks", broker="redis://localhost")

@celery_app.task
def process_order(order_id: str):
    # Heavy processing
    pass

@app.post("/order")
async def create_order(request):
    data = await request.json()
    process_order.delay(data["id"])
    return {"status": "queued"}
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: "3.8"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: app
    volumes:
      - postgres_data:/var/lib/postgresql/data
volumes:
  postgres_data:
```
