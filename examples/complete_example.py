"""
Complete example demonstrating all QakeAPI features.

This example shows:
- Basic routes
- Path and query parameters
- Request body parsing
- Dependency injection
- Validation
- Security (JWT, CORS)
- Caching
- WebSocket
- Templates
"""

from qakeapi import (
    QakeAPI,
    Request,
    JSONResponse,
    Depends,
    WebSocket,
    NotFound,
)
from qakeapi.validation import BaseModel, Field, StringValidator, IntegerValidator
from qakeapi.security import AuthManager, CORSMiddleware
from qakeapi.caching import CacheMiddleware, MemoryCache
from qakeapi.utils import TemplateRenderer, mount_static


# Create application
app = QakeAPI(
    title="Complete Example API",
    version="1.1.0",
    description="Complete example demonstrating all QakeAPI features",
    debug=True,
)

# Add CORS middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Add caching middleware
cache = MemoryCache()
app.add_middleware(CacheMiddleware, cache=cache, ttl=60)

# Initialize auth manager
auth_manager = AuthManager(secret_key="your-secret-key-here")


# Data models
class UserCreate(BaseModel):
    name: str
    email: str
    age: int


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    age: int


# Mock database
users_db = []
user_counter = 0


# Dependencies
async def get_current_user(request: Request):
    """Get current user from request."""
    # In real app, extract from JWT token
    return {"id": 1, "name": "Test User"}


# Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to QakeAPI!",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/users")
async def get_users(limit: int = 10, offset: int = 0):
    """Get all users with pagination."""
    return {
        "users": users_db[offset:offset + limit],
        "total": len(users_db),
        "limit": limit,
        "offset": offset,
    }


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID."""
    for user in users_db:
        if user["id"] == user_id:
            return user
    raise NotFound(f"User {user_id} not found")


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
    users_db.append(user_data)
    
    return JSONResponse(user_data, status_code=201)


@app.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return {"user": current_user}


@app.post("/login")
async def login(request: Request):
    """Login endpoint."""
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    
    # In real app, verify credentials
    if username == "admin" and password == "password":
        token = auth_manager.create_access_token({"username": username, "user_id": 1})
        return {"access_token": token, "token_type": "bearer"}
    
    return JSONResponse({"detail": "Invalid credentials"}, status_code=401)


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket chat endpoint."""
    await websocket.accept()
    
    await websocket.send_json({
        "type": "connection",
        "message": "Connected to WebSocket!",
    })
    
    try:
        async for message in websocket.iter_json():
            # Echo message back
            await websocket.send_json({
                "type": "echo",
                "data": message,
            })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


# Lifecycle events
@app.on_event("startup")
async def startup():
    """Run on application startup."""
    print("Application starting...")


@app.on_event("shutdown")
async def shutdown():
    """Run on application shutdown."""
    print("Application shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

