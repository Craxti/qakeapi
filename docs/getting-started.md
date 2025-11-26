# Getting Started with QakeAPI

This guide will help you get started with QakeAPI 1.2.0.

## Installation

```bash
pip install qakeapi
```

Or install from source:

```bash
git clone https://github.com/craxti/qakeapi.git
cd qakeapi
pip install -e .
```

## Your First Application

Create a file `main.py`:

```python
from qakeapi import QakeAPI, CORSMiddleware

app = QakeAPI(
    title="My First API",
    version="1.2.0",
    description="My first QakeAPI application"
)

# Add CORS middleware
app.add_middleware(CORSMiddleware(allow_origins=["*"]))

@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Hello, QakeAPI!"}

@app.get("/users/{id}")
def get_user(id: int):
    """Get user by ID."""
    return {"id": id, "name": f"User {id}"}

@app.post("/users")
async def create_user(request):
    """Create a new user."""
    data = await request.json()
    return {"message": "User created", "data": data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run the application:

```bash
python main.py
```

Visit:
- API: `http://localhost:8000/`
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Key Concepts

### 1. Hybrid Sync/Async

QakeAPI automatically handles both synchronous and asynchronous functions:

```python
# Sync function - automatically converted to async
@app.get("/sync")
def sync_handler():
    return {"type": "sync"}

# Async function - works normally
@app.get("/async")
async def async_handler():
    return {"type": "async"}
```

### 2. Request Handling

Access request data:

```python
@app.post("/data")
async def handle_data(request):
    # Get JSON body
    data = await request.json()
    
    # Get query parameters
    limit = request.get_query_param("limit", default=10)
    
    # Get headers
    content_type = request.headers.get("content-type")
    
    return {"received": data}
```

### 3. Response Types

Return different response types:

```python
from qakeapi.core.response import JSONResponse, HTMLResponse

@app.get("/json")
def json_response():
    return {"message": "JSON response"}

@app.get("/html")
def html_response():
    return HTMLResponse("<h1>Hello</h1>")

@app.get("/error")
def error_response():
    return {"error": "Not found"}, 404
```

### 4. Dependency Injection

Use dependency injection for cleaner code:

```python
from qakeapi import QakeAPI, Depends

app = QakeAPI()

def get_database():
    return Database()

@app.get("/users")
async def get_users(db = Depends(get_database)):
    return await db.get_users()
```

See the [Dependency Injection Guide](dependency-injection.md) for more details.

### 5. Request Size Validation

Protect your API from large requests:

```python
from qakeapi import QakeAPI, RequestSizeLimitMiddleware

app = QakeAPI()
app.add_middleware(RequestSizeLimitMiddleware(max_size=10 * 1024 * 1024))  # 10MB
```

## Next Steps

- Read the [Routing Guide](routing.md) to learn about routing and performance optimizations
- Check out [Dependency Injection](dependency-injection.md) for cleaner architecture
- Explore [Middleware](middleware.md) for request/response processing
- Check out [Examples](../examples/) for more complex examples
- Explore the [API Reference](api-reference.md) for complete documentation


