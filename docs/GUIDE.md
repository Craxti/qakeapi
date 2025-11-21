# QakeAPI Guide

Complete guide to using QakeAPI framework.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Routing](#routing)
3. [Request Handling](#request-handling)
4. [Response Types](#response-types)
5. [Validation](#validation)
6. [Dependency Injection](#dependency-injection)
7. [Middleware](#middleware)
8. [WebSocket](#websocket)
9. [Security](#security)
10. [Testing](#testing)

## Getting Started

### Installation

```bash
pip install -e .
```

### Basic Application

```python
from qakeapi import QakeAPI

app = QakeAPI(title="My API")

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Routing

### Path Parameters

```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}
```

### Query Parameters

```python
@app.get("/items")
async def get_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}
```

### Multiple HTTP Methods

```python
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}

@app.post("/items")
async def create_item(request: Request):
    data = await request.json()
    return {"created": data}

@app.put("/items/{item_id}")
async def update_item(item_id: int, request: Request):
    data = await request.json()
    return {"updated": item_id, "data": data}

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    return {"deleted": item_id}
```

## Request Handling

### JSON Body

```python
@app.post("/users")
async def create_user(request: Request):
    data = await request.json()
    return {"user": data}
```

### Form Data

```python
@app.post("/upload")
async def upload(request: Request):
    form = await request.form()
    return {"form": dict(form)}
```

### Headers

```python
@app.get("/")
async def root(request: Request):
    auth = request.headers.get("authorization")
    return {"auth": auth}
```

### Cookies

```python
@app.get("/")
async def root(request: Request):
    session = request.cookies.get("session")
    return {"session": session}
```

## Response Types

### JSON Response

```python
from qakeapi import JSONResponse

@app.get("/")
async def root():
    return JSONResponse({"message": "Hello"}, status_code=200)
```

### HTML Response

```python
from qakeapi import HTMLResponse

@app.get("/")
async def home():
    return HTMLResponse("<h1>Home</h1>")
```

### Redirect

```python
from qakeapi import RedirectResponse

@app.get("/old")
async def old():
    return RedirectResponse("/new", status_code=301)
```

### File Response

```python
from qakeapi import FileResponse

@app.get("/download")
async def download():
    return FileResponse(
        path="/path/to/file.pdf",
        filename="document.pdf",
        media_type="application/pdf",
    )
```

## Validation

### Using BaseModel

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

### Field Validation

```python
class Item(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(min_value=0.0)
    quantity: int = Field(min_value=0)
    tags: list = Field(default=[])
```

## Dependency Injection

### Basic Dependency

```python
from qakeapi import Depends

async def get_database():
    return {"connected": True}

@app.get("/")
async def root(db: dict = Depends(get_database)):
    return {"database": db}
```

### Dependency with Request

```python
async def get_current_user(request: Request):
    token = request.headers.get("authorization", "")
    # Verify token and return user
    return {"user_id": 1, "username": "admin"}

@app.get("/profile")
async def profile(user: dict = Depends(get_current_user)):
    return {"user": user}
```

### Nested Dependencies

```python
async def get_db():
    return {"db": "connected"}

async def get_user(db: dict = Depends(get_db)):
    return {"user_id": 1}

@app.get("/")
async def root(user: dict = Depends(get_user)):
    return {"user": user}
```

## Middleware

### Adding Middleware

```python
from qakeapi.security import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
)
```

### Custom Middleware

```python
from qakeapi.core.middleware import BaseMiddleware

class CustomMiddleware(BaseMiddleware):
    async def process_http(self, scope, receive, send):
        # Before request
        print("Before request")
        
        # Process request
        if self.app:
            await self.app(scope, receive, send)
        
        # After request
        print("After request")

app.add_middleware(CustomMiddleware)
```

## WebSocket

### Basic WebSocket

```python
from qakeapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    await websocket.send_json({"message": "Connected"})
    
    async for message in websocket.iter_json():
        await websocket.send_json({"echo": message})
    
    await websocket.close()
```

### WebSocket with Authentication

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Check authentication
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    
    await websocket.accept()
    
    try:
        async for message in websocket.iter_json():
            # Process message
            await websocket.send_json({"response": message})
    finally:
        await websocket.close()
```

## Security

### Authentication

```python
from qakeapi.security import AuthManager

auth_manager = AuthManager(secret_key="your-secret-key")

@app.post("/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    
    # Verify credentials
    if verify_user(username, password):
        token = auth_manager.create_access_token({"username": username})
        return {"access_token": token}
    
    return JSONResponse({"error": "Invalid credentials"}, status_code=401)

@app.get("/protected")
async def protected(request: Request):
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    payload = auth_manager.verify_token(token)
    
    if not payload:
        return JSONResponse({"error": "Invalid token"}, status_code=401)
    
    return {"data": "protected"}
```

### CORS

```python
from qakeapi.security import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
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
            headers={"Retry-After": str(retry_after)},
        )
    
    return {"message": "OK"}
```

## Testing

### Using TestClient

```python
from qakeapi import QakeAPI
from qakeapi.testing import TestClient

app = QakeAPI()

@app.get("/")
async def root():
    return {"message": "Hello"}

# Test
def test_root():
    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}
```

### Testing with Authentication

```python
def test_protected():
    client = TestClient(app)
    
    # Login
    login_response = client.post(
        "/login",
        json={"username": "admin", "password": "password"},
    )
    token = login_response.json()["access_token"]
    
    # Access protected endpoint
    response = client.get(
        "/protected",
        headers={"authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
```

## Best Practices

1. **Use async/await** - All handlers should be async
2. **Validate input** - Always validate user input using BaseModel
3. **Handle errors** - Use exception handlers for error handling
4. **Use dependencies** - Extract common logic into dependencies
5. **Test your code** - Write tests using TestClient
6. **Secure your API** - Use authentication and rate limiting
7. **Document your API** - OpenAPI docs are auto-generated

