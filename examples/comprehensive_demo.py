"""
Comprehensive QakeAPI Demo

This example demonstrates all major features of QakeAPI:
- Different HTTP methods (GET, POST, PUT, DELETE, PATCH)
- Path and query parameters
- Request body parsing (JSON, form-data)
- Validation with BaseModel
- Dependency injection
- Authentication with JWT
- CORS middleware
- Caching
- Error handling
- WebSocket
- Static files serving
- Template rendering
"""

from qakeapi import (
    QakeAPI,
    Request,
    JSONResponse,
    HTMLResponse,
    Depends,
    WebSocket,
    NotFound,
    BadRequest,
)
from qakeapi.validation import (
    BaseModel,
    Field,
    StringValidator,
    IntegerValidator,
    EmailValidator,
    ValidationError,
)
from qakeapi.security import AuthManager, CORSMiddleware
from qakeapi.caching import MemoryCache, CacheMiddleware
from qakeapi.utils import TemplateRenderer
import tempfile
import os
from pathlib import Path


# Create application
app = QakeAPI(
    title="Comprehensive QakeAPI Demo",
    version="1.1.0",
    description="Complete example demonstrating all QakeAPI features",
    debug=True,
)

# Add CORS middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Add caching middleware
cache = MemoryCache(default_ttl=300)
app.add_middleware(CacheMiddleware, cache=cache, ttl=60)

# Initialize auth manager
auth_manager = AuthManager(secret_key="demo-secret-key-change-in-production")


# ============================================================================
# Data Models
# ============================================================================

class UserCreate(BaseModel):
    """User creation model."""
    name: str = Field(validator=StringValidator(min_length=2, max_length=50))
    email: str = Field(validator=EmailValidator())
    age: int = Field(validator=IntegerValidator(min_value=18, max_value=120))


class UserUpdate(BaseModel):
    """User update model."""
    name: str = Field(validator=StringValidator(min_length=2, max_length=50), required=False)
    email: str = Field(validator=EmailValidator(), required=False)
    age: int = Field(validator=IntegerValidator(min_value=18, max_value=120), required=False)


class ItemCreate(BaseModel):
    """Item creation model."""
    name: str = Field(validator=StringValidator(min_length=1, max_length=100))
    price: float = Field(validator=IntegerValidator(min_value=0))
    description: str = Field(validator=StringValidator(max_length=500), required=False)


# ============================================================================
# Mock Database
# ============================================================================

users_db = {}
items_db = {}
user_counter = 0
item_counter = 0

# Sample data
users_db[1] = {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30}
users_db[2] = {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25}
user_counter = 2

items_db[1] = {"id": 1, "name": "Laptop", "price": 999.99, "description": "High-performance laptop"}
items_db[2] = {"id": 2, "name": "Mouse", "price": 29.99, "description": "Wireless mouse"}
item_counter = 2


# ============================================================================
# Dependencies
# ============================================================================

async def get_current_user(request: Request):
    """Get current user from JWT token."""
    auth_header = request.headers.get("authorization", "")
    
    if not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header[7:]
    payload = auth_manager.verify_token(token)
    
    if payload and "user_id" in payload:
        user_id = payload["user_id"]
        return users_db.get(user_id)
    
    return None


async def require_auth(current_user: dict = Depends(get_current_user)):
    """Require authentication."""
    if current_user is None:
        raise BadRequest("Authentication required")
    return current_user


# ============================================================================
# Root and Info Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to QakeAPI Comprehensive Demo!",
        "version": "1.1.0",
        "endpoints": {
            "users": "/users",
            "items": "/items",
            "auth": "/login",
            "websocket": "/ws",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "users_count": len(users_db),
        "items_count": len(items_db),
    }


# ============================================================================
# User Endpoints
# ============================================================================

@app.get("/users")
async def get_users(skip: int = 0, limit: int = 10):
    """
    Get all users with pagination.
    
    Query parameters:
    - skip: Number of users to skip (default: 0)
    - limit: Maximum number of users to return (default: 10)
    """
    users_list = list(users_db.values())
    return {
        "users": users_list[skip:skip + limit],
        "total": len(users_list),
        "skip": skip,
        "limit": limit,
    }


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID."""
    if user_id not in users_db:
        raise NotFound(f"User {user_id} not found")
    return users_db[user_id]


@app.post("/users")
async def create_user(user: UserCreate):
    """Create a new user."""
    global user_counter
    user_counter += 1
    
    user_data = {
        "id": user_counter,
        "name": user.name,
        "email": user.email,
        "age": user.age,
    }
    users_db[user_counter] = user_data
    
    return JSONResponse(user_data, status_code=201)


@app.put("/users/{user_id}")
async def update_user(user_id: int, user: UserUpdate, current_user: dict = Depends(require_auth)):
    """Update user (requires authentication)."""
    if user_id not in users_db:
        raise NotFound(f"User {user_id} not found")
    
    # Update only provided fields
    updates = user.dict(exclude_none=True)
    users_db[user_id].update(updates)
    
    return users_db[user_id]


@app.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(require_auth)):
    """Delete user (requires authentication)."""
    if user_id not in users_db:
        raise NotFound(f"User {user_id} not found")
    
    deleted_user = users_db.pop(user_id)
    return {"message": "User deleted", "user": deleted_user}


@app.patch("/users/{user_id}/age")
async def update_user_age(user_id: int, request: Request):
    """Update user age using PATCH method."""
    if user_id not in users_db:
        raise NotFound(f"User {user_id} not found")
    
    data = await request.json()
    new_age = data.get("age")
    
    if new_age is None:
        raise BadRequest("Age is required")
    
    if not isinstance(new_age, int) or new_age < 18 or new_age > 120:
        raise BadRequest("Age must be between 18 and 120")
    
    users_db[user_id]["age"] = new_age
    return users_db[user_id]


# ============================================================================
# Item Endpoints
# ============================================================================

@app.get("/items")
async def get_items(category: str = None, min_price: float = None, max_price: float = None):
    """
    Get all items with optional filtering.
    
    Query parameters:
    - category: Filter by category (not implemented in demo)
    - min_price: Minimum price filter
    - max_price: Maximum price filter
    """
    items_list = list(items_db.values())
    
    # Apply filters
    if min_price is not None:
        items_list = [item for item in items_list if item["price"] >= min_price]
    
    if max_price is not None:
        items_list = [item for item in items_list if item["price"] <= max_price]
    
    return {
        "items": items_list,
        "total": len(items_list),
    }


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Get item by ID."""
    if item_id not in items_db:
        raise NotFound(f"Item {item_id} not found")
    return items_db[item_id]


@app.post("/items")
async def create_item(item: ItemCreate):
    """Create a new item."""
    global item_counter
    item_counter += 1
    
    item_data = {
        "id": item_counter,
        "name": item.name,
        "price": item.price,
        "description": item.description or "",
    }
    items_db[item_counter] = item_data
    
    return JSONResponse(item_data, status_code=201)


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: ItemCreate):
    """Update item."""
    if item_id not in items_db:
        raise NotFound(f"Item {item_id} not found")
    
    items_db[item_id].update({
        "name": item.name,
        "price": item.price,
        "description": item.description or "",
    })
    
    return items_db[item_id]


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete item."""
    if item_id not in items_db:
        raise NotFound(f"Item {item_id} not found")
    
    deleted_item = items_db.pop(item_id)
    return {"message": "Item deleted", "item": deleted_item}


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/login")
async def login(request: Request):
    """Login endpoint - returns JWT token."""
    try:
        data = await request.json()
    except (ValueError, Exception):
        # Handle empty or invalid JSON
        data = {}
    
    username = data.get("username")
    password = data.get("password")
    
    # Simple authentication (in production, verify against database)
    if username == "admin" and password == "password":
        token = auth_manager.create_access_token({"user_id": 1, "username": "admin"})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": users_db[1],
        }
    
    return JSONResponse(
        {"detail": "Invalid credentials"},
        status_code=401,
    )


@app.get("/me")
async def get_current_user_info(current_user: dict = Depends(require_auth)):
    """Get current authenticated user info."""
    return {
        "user": current_user,
        "message": "You are authenticated!",
    }


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket chat endpoint."""
    await websocket.accept()
    
    await websocket.send_json({
        "type": "connection",
        "message": "Connected to QakeAPI WebSocket!",
        "commands": {
            "echo": "Send any message to echo it back",
            "users": "Get user count",
            "items": "Get item count",
            "help": "Show this help message",
        },
    })
    
    try:
        async for message in websocket.iter_json():
            msg_type = message.get("type", "")
            text = message.get("text", "")
            
            if msg_type == "echo" or not msg_type:
                # Echo message
                await websocket.send_json({
                    "type": "echo",
                    "original": message,
                    "response": f"Echo: {text}",
                })
            elif msg_type == "users":
                # Get user count
                await websocket.send_json({
                    "type": "response",
                    "data": {"users_count": len(users_db)},
                })
            elif msg_type == "items":
                # Get item count
                await websocket.send_json({
                    "type": "response",
                    "data": {"items_count": len(items_db)},
                })
            elif msg_type == "help":
                # Show help
                await websocket.send_json({
                    "type": "help",
                    "commands": ["echo", "users", "items", "help"],
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown command: {msg_type}",
                })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


# ============================================================================
# Form Data Endpoint
# ============================================================================

@app.post("/upload")
async def upload_file(request: Request):
    """Handle file upload (form-data)."""
    form = await request.form()
    
    return {
        "message": "File upload endpoint",
        "form_data": dict(form),
        "note": "In production, save files to disk/storage",
    }


# ============================================================================
# HTML Response Endpoint
# ============================================================================

@app.get("/demo")
async def demo_page():
    """Demo HTML page."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>QakeAPI Demo</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .method { display: inline-block; padding: 3px 8px; border-radius: 3px; font-weight: bold; }
            .get { background: #4CAF50; color: white; }
            .post { background: #2196F3; color: white; }
            .put { background: #FF9800; color: white; }
            .delete { background: #F44336; color: white; }
            code { background: #eee; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>QakeAPI Comprehensive Demo</h1>
        <p>This demo showcases all major features of QakeAPI framework.</p>
        
        <h2>Available Endpoints</h2>
        
        <div class="endpoint">
            <span class="method get">GET</span> <code>/</code> - API information
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span> <code>/users</code> - Get all users
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span> <code>/users/{id}</code> - Get user by ID
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <code>/users</code> - Create user
        </div>
        
        <div class="endpoint">
            <span class="method put">PUT</span> <code>/users/{id}</code> - Update user (auth required)
        </div>
        
        <div class="endpoint">
            <span class="method delete">DELETE</span> <code>/users/{id}</code> - Delete user (auth required)
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span> <code>/items</code> - Get all items
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <code>/items</code> - Create item
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <code>/login</code> - Login (username: admin, password: password)
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span> <code>/me</code> - Get current user (auth required)
        </div>
        
        <h2>Documentation</h2>
        <p><a href="/docs">Swagger UI</a> | <a href="/redoc">ReDoc</a> | <a href="/openapi.json">OpenAPI JSON</a></p>
        
        <h2>WebSocket</h2>
        <p>Connect to <code>ws://localhost:8000/ws</code> for WebSocket demo</p>
    </body>
    </html>
    """
    return HTMLResponse(html_content)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    return JSONResponse(
        {
            "detail": str(exc),
            "field": exc.field,
        },
        status_code=422,
    )


@app.exception_handler(NotFound)
async def not_found_handler(request: Request, exc: NotFound):
    """Handle 404 errors."""
    return JSONResponse(
        {"detail": str(exc), "path": request.path},
        status_code=404,
    )


# ============================================================================
# Documentation Endpoints
# ============================================================================
# IMPORTANT: /docs, /redoc, and /openapi.json are automatically handled by QakeAPI
# in application.py BEFORE routes are processed (see lines 184-194 in application.py).
# This means explicit routes here will NEVER be reached!
#
# The automatic handlers use:
# - app._handle_openapi() for /openapi.json
# - app._handle_swagger_ui() for /docs  
# - app._handle_redoc() for /redoc
#
# So we don't need to define them here. They work automatically!

# If you want to customize, you would need to modify the application class
# or change the URLs (app.openapi_url, app.docs_url, app.redoc_url)


# ============================================================================
# Lifecycle Events
# ============================================================================


@app.on_event("startup")
async def startup():
    """Run on application startup."""
    print("QakeAPI Comprehensive Demo starting...")
    print("=" * 60)
    print("Documentation:")
    print("   Swagger UI:  http://localhost:8000/docs")
    print("   ReDoc:       http://localhost:8000/redoc")
    print("   OpenAPI JSON: http://localhost:8000/openapi.json")
    print("=" * 60)
    print("Demo page:   http://localhost:8000/demo")
    print("WebSocket:   ws://localhost:8000/ws")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown():
    """Run on application shutdown."""
    print("QakeAPI Comprehensive Demo shutting down...")


# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("Starting QakeAPI Comprehensive Demo")
    print("="*60)
    print("\nAvailable endpoints:")
    print("  GET  /              - API information")
    print("  GET  /health        - Health check")
    print("  GET  /demo          - Demo HTML page")
    print("  GET  /users         - List users")
    print("  GET  /users/{id}    - Get user")
    print("  POST /users         - Create user")
    print("  PUT  /users/{id}    - Update user (auth required)")
    print("  DELETE /users/{id}  - Delete user (auth required)")
    print("  GET  /items         - List items")
    print("  POST /items         - Create item")
    print("  POST /login         - Login (admin/password)")
    print("  GET  /me            - Current user (auth required)")
    print("  WS   /ws            - WebSocket chat")
    print("\nDocumentation:")
    print("  http://localhost:8000/docs      - Swagger UI")
    print("  http://localhost:8000/redoc     - ReDoc")
    print("  http://localhost:8000/openapi.json - OpenAPI JSON")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

