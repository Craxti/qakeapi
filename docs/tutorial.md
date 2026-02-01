# QakeAPI Tutorial: From Zero to Deploy

This tutorial walks you through building a REST API with QakeAPI from scratch to deployment.

## Step 1: Installation

```bash
pip install qakeapi uvicorn
```

## Step 2: Create Your First Endpoint

Create `main.py`:

```python
from qakeapi import QakeAPI

app = QakeAPI(title="My API", version="1.0.0")

@app.get("/")
def root():
    return {"message": "Hello, QakeAPI!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run:

```bash
python main.py
```

Visit `http://localhost:8000/` and `http://localhost:8000/docs` for Swagger UI.

## Step 3: Add Path and Query Parameters

```python
@app.get("/users/{id}")
def get_user(id: int):
    return {"id": id, "name": f"User {id}"}

@app.get("/search")
def search(q: str, limit: int = 10):
    return {"query": q, "limit": limit, "results": []}
```

## Step 4: Add POST with Request Body

```python
@app.post("/users")
async def create_user(request):
    data = await request.json()
    return {"message": "Created", "data": data}
```

## Step 5: Add CORS and Middleware

```python
from qakeapi import QakeAPI, CORSMiddleware, LoggingMiddleware

app = QakeAPI(title="My API", version="1.0.0")
app.add_middleware(CORSMiddleware(allow_origins=["*"]))
app.add_middleware(LoggingMiddleware())
```

## Step 6: Add Dependency Injection

```python
from qakeapi import Depends

def get_db():
    return {"connection": "sqlite"}

@app.get("/users")
def get_users(db = Depends(get_db)):
    return {"users": [], "db": db}
```

## Step 7: Add Caching

```python
from qakeapi import cache

@cache(ttl=60)
@app.get("/expensive")
def expensive():
    return {"result": "computed"}
```

## Step 8: Add Rate Limiting

```python
from qakeapi import rate_limit

@rate_limit(requests_per_minute=60)
@app.get("/api/data")
def get_data():
    return {"data": "..."}
```

## Step 9: Add Background Tasks

```python
from qakeapi.core.background import add_background_task

@app.post("/process")
async def process(request):
    data = await request.json()
    await add_background_task(send_email, data["email"])
    return {"status": "processing"}
```

## Step 10: Deploy with Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `requirements.txt`:

```
qakeapi
uvicorn[standard]
```

Build and run:

```bash
docker build -t my-api .
docker run -p 8000:8000 my-api
```

## Next Steps

- [Getting Started](getting-started.md)
- [API Reference](api-reference.md)
- [Benchmarks](benchmarks.md)
- [Ecosystem](ecosystem.md)
