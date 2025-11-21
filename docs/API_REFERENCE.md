# API Reference

Complete API reference for QakeAPI framework.

## Core Components

### QakeAPI

Main application class.

```python
from qakeapi import QakeAPI

app = QakeAPI(
    title="My API",
    version="1.0.0",
    description="API description",
    debug=False,
)
```

**Parameters:**
- `title` (str): Application title
- `version` (str): Application version
- `description` (str): Application description
- `debug` (bool): Enable debug mode

**Methods:**
- `@app.get(path)` - Register GET route
- `@app.post(path)` - Register POST route
- `@app.put(path)` - Register PUT route
- `@app.delete(path)` - Register DELETE route
- `@app.patch(path)` - Register PATCH route
- `@app.websocket(path)` - Register WebSocket route
- `app.add_middleware(middleware_class, **kwargs)` - Add middleware
- `app.include_router(router)` - Include router
- `@app.on_event("startup")` - Startup event handler
- `@app.on_event("shutdown")` - Shutdown event handler
- `@app.exception_handler(exception_class)` - Exception handler

### Request

HTTP request object.

```python
from qakeapi import Request

@app.post("/items")
async def create_item(request: Request):
    # Get JSON body
    data = await request.json()
    
    # Get form data
    form = await request.form()
    
    # Get query parameters
    query = request.query_params
    
    # Get path parameters
    user_id = request.get_path_param("user_id")
    
    # Get headers
    auth = request.headers.get("authorization")
    
    # Get cookies
    session = request.cookies.get("session")
```

### Response

Response classes.

```python
from qakeapi import (
    Response,
    JSONResponse,
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
    FileResponse,
)

# JSON response
return JSONResponse({"message": "Hello"}, status_code=200)

# HTML response
return HTMLResponse("<h1>Hello</h1>")

# Plain text
return PlainTextResponse("Hello")

# Redirect
return RedirectResponse("/new-url", status_code=302)

# File
return FileResponse(path="/path/to/file.pdf", filename="file.pdf")
```

### Router

```python
from qakeapi import APIRouter

router = APIRouter()

@router.get("/users")
async def get_users():
    return {"users": []}

# Include in app
app.include_router(router)
```

### Dependency Injection

```python
from qakeapi import Depends

async def get_database():
    return {"connected": True}

@app.get("/")
async def root(db: dict = Depends(get_database)):
    return {"database": db}
```

### WebSocket

```python
from qakeapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Send message
    await websocket.send_json({"message": "Hello"})
    
    # Receive message
    message = await websocket.receive_json()
    
    # Iterate messages
    async for message in websocket.iter_json():
        await websocket.send_json({"echo": message})
    
    await websocket.close()
```

## Validation

### BaseModel

```python
from qakeapi.validation import BaseModel, Field

class UserCreate(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    email: str = Field(regex=r"^[^@]+@[^@]+\.[^@]+$")
    age: int = Field(min_value=18, max_value=120)

@app.post("/users")
async def create_user(user: UserCreate):
    return {"user": user.dict()}
```

### Validators

```python
from qakeapi.validation import (
    StringValidator,
    IntegerValidator,
    EmailValidator,
    URLValidator,
)

validator = EmailValidator()
is_valid = validator.validate("user@example.com")
```

## Security

### AuthManager

```python
from qakeapi.security import AuthManager

auth_manager = AuthManager(secret_key="secret-key")

# Hash password
hashed = auth_manager.hash_password("password123")

# Verify password
is_valid = auth_manager.verify_password("password123", hashed)

# Create token
token = auth_manager.create_access_token({"user_id": 1})

# Verify token
payload = auth_manager.verify_token(token)
```

### CORS

```python
from qakeapi.security import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Rate Limiting

```python
from qakeapi.security import RateLimiter

limiter = RateLimiter(requests_per_minute=60)

@app.get("/api")
async def api_endpoint(request: Request):
    client_ip = request.client[0]
    allowed, retry_after = limiter.is_allowed(client_ip)
    
    if not allowed:
        return JSONResponse(
            {"error": "Rate limit exceeded"},
            status_code=429,
        )
    
    return {"message": "OK"}
```

## Caching

```python
from qakeapi.caching import MemoryCache, CacheMiddleware

cache = MemoryCache(default_ttl=300)

app.add_middleware(CacheMiddleware, cache=cache, ttl=60)

# Manual caching
cache.set("key", "value", ttl=60)
value = cache.get("key")
cache.delete("key")
```

## Testing

```python
from qakeapi import QakeAPI
from qakeapi.testing import TestClient

app = QakeAPI()

@app.get("/")
async def root():
    return {"message": "Hello"}

# Test
client = TestClient(app)
response = client.get("/")
assert response.status_code == 200
assert response.json() == {"message": "Hello"}
```

## Utilities

### Static Files

```python
from qakeapi.utils import StaticFiles, mount_static

# Mount static files
mount_static(app, path="/static", directory="./static")

# Or use directly
static = StaticFiles(directory="./static", path="/static")
```

### Templates

```python
from qakeapi.utils import TemplateRenderer

renderer = TemplateRenderer(directory="./templates")

@app.get("/")
async def home():
    return renderer.TemplateResponse(
        "index.html",
        context={"title": "Home"},
    )
```

## Exceptions

```python
from qakeapi import HTTPException, NotFound, BadRequest

# Raise exception
raise NotFound("Resource not found")
raise BadRequest("Invalid input")
raise HTTPException(500, "Internal error")

# Custom exception handler
@app.exception_handler(NotFound)
async def not_found_handler(request: Request, exc: NotFound):
    return JSONResponse(
        {"error": str(exc)},
        status_code=404,
    )
```

