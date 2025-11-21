"""
QakeAPI Complete API Example

This is a comprehensive example showing all major features of QakeAPI working together.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from qakeapi import Depends, QakeAPI, Request, WebSocket
from qakeapi.caching.cache import CacheManager, InMemoryCache
from qakeapi.caching.middleware import CacheMiddleware
from qakeapi.core.exceptions import HTTPException
from qakeapi.middleware.auth import BearerTokenMiddleware
from qakeapi.middleware.compression import CompressionMiddleware
from qakeapi.middleware.cors import CORSMiddleware
from qakeapi.middleware.logging import LoggingMiddleware
from qakeapi.monitoring.health import (
    HealthChecker,
    HealthCheckMiddleware,
    MemoryHealthCheck,
)
from qakeapi.monitoring.metrics import MetricsCollector, MetricsMiddleware
from qakeapi.security.rate_limiting import (
    RateLimiter,
    RateLimitMiddleware,
    RateLimitRule,
)
from qakeapi.utils.status import status


# Data Models
class User(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool = True


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=8)


class Product(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)


# Create application
app = QakeAPI(
    title="Complete QakeAPI Example",
    description="Comprehensive example showing all QakeAPI features",
    version="1.0.0",
    debug=True,
)

# Initialize components
metrics = MetricsCollector()
health_checker = HealthChecker()
health_checker.add_check(MemoryHealthCheck())
cache = InMemoryCache(max_size=1000)
cache_manager = CacheManager(backend=cache)
rate_limiter = RateLimiter()
rate_limiter.add_rule("/api/*", RateLimitRule(requests=100, window=60))

# Add middleware (order matters!)
app.add_middleware(
    CORSMiddleware(allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
)
app.add_middleware(LoggingMiddleware())
app.add_middleware(CompressionMiddleware(minimum_size=500))
app.add_middleware(MetricsMiddleware(collector=metrics))
app.add_middleware(HealthCheckMiddleware(health_checker=health_checker))
app.add_middleware(
    CacheMiddleware(
        cache_manager=cache_manager,
        cache_methods={"GET"},
        default_expire=300,
        skip_paths={"/health", "/metrics"},
    )
)
app.add_middleware(
    RateLimitMiddleware(
        rate_limiter=rate_limiter,
        skip_paths={"/", "/health", "/docs", "/redoc"},
    )
)
app.add_middleware(
    BearerTokenMiddleware(
        secret_key="your-secret-key-change-in-production",
        skip_paths={
            "/",
            "/login",
            "/register",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        },
    )
)

# In-memory storage (use database in production)
users_db: dict[int, User] = {}
products_db: dict[int, Product] = {}
user_counter = 0
product_counter = 0

# WebSocket connections
websocket_clients: set[WebSocket] = set()


# Dependency: Get current user
async def get_current_user(request: Request) -> dict:
    """Get current authenticated user"""
    user_info = getattr(request, "_user", None)
    if not user_info:
        raise HTTPException(status.UNAUTHORIZED, "Authentication required")
    return user_info


# Authentication endpoints
@app.post("/register")
async def register(user_data: UserCreate):
    """Register a new user"""
    global user_counter

    # Check if username or email already exists
    for user in users_db.values():
        if user.username == user_data.username:
            raise HTTPException(status.BAD_REQUEST, "Username already exists")
        if user.email == user_data.email:
            raise HTTPException(status.BAD_REQUEST, "Email already exists")

    user_counter += 1
    user = User(
        id=user_counter,
        username=user_data.username,
        email=user_data.email,
    )
    users_db[user.id] = user

    return {"message": "User registered successfully", "user_id": user.id}


@app.post("/login")
async def login(request: Request):
    """Login and get JWT token"""
    data = await request.json()
    username = data.get("username")
    password = data.get("password")

    # Find user (in production, verify password hash)
    user = None
    for u in users_db.values():
        if u.username == username:
            user = u
            break

    if not user:
        raise HTTPException(status.UNAUTHORIZED, "Invalid credentials")

    # In production, generate real JWT token
    token = f"fake-jwt-token-for-{user.id}"

    return {"access_token": token, "token_type": "bearer", "user_id": user.id}


# User endpoints
@app.get("/users/")
async def get_users(current_user: dict = Depends(get_current_user)):
    """Get all users (cached, rate limited, requires auth)"""
    return list(users_db.values())


@app.get("/users/{user_id}")
async def get_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get user by ID (cached, rate limited, requires auth)"""
    if user_id not in users_db:
        raise HTTPException(status.NOT_FOUND, "User not found")
    return users_db[user_id]


# Product endpoints
@app.get("/products/")
async def get_products():
    """Get all products (cached, rate limited)"""
    return list(products_db.values())


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    """Get product by ID (cached, rate limited)"""
    if product_id not in products_db:
        raise HTTPException(status.NOT_FOUND, "Product not found")
    return products_db[product_id]


@app.post("/products/")
async def create_product(
    product_data: ProductCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create new product (requires auth, invalidates cache)"""
    global product_counter

    product_counter += 1
    product = Product(
        id=product_counter,
        **product_data.dict(),
    )
    products_db[product.id] = product

    # Invalidate cache
    await cache_manager.delete("GET:/products/")

    return product


@app.put("/products/{product_id}")
async def update_product(
    product_id: int,
    product_data: ProductCreate,
    current_user: dict = Depends(get_current_user),
):
    """Update product (requires auth, invalidates cache)"""
    if product_id not in products_db:
        raise HTTPException(status.NOT_FOUND, "Product not found")

    product = Product(id=product_id, **product_data.dict())
    products_db[product_id] = product

    # Invalidate cache
    await cache_manager.delete(f"GET:/products/{product_id}")
    await cache_manager.delete("GET:/products/")

    return product


@app.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Delete product (requires auth, invalidates cache)"""
    if product_id not in products_db:
        raise HTTPException(status.NOT_FOUND, "Product not found")

    del products_db[product_id]

    # Invalidate cache
    await cache_manager.delete(f"GET:/products/{product_id}")
    await cache_manager.delete("GET:/products/")

    return {"message": "Product deleted"}


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_clients.add(websocket)

    try:
        await websocket.send_json(
            {
                "type": "connection",
                "message": "Connected to QakeAPI",
                "clients_count": len(websocket_clients),
            }
        )

        async for message in websocket.iter_json():
            # Broadcast message to all clients
            for client in websocket_clients.copy():
                try:
                    await client.send_json(
                        {
                            "type": "broadcast",
                            "data": message,
                        }
                    )
                except:
                    websocket_clients.discard(client)

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        websocket_clients.discard(websocket)


# Monitoring endpoints
@app.get("/health")
async def health():
    """Health check endpoint"""
    results = await health_checker.check_all()
    return {
        "status": "healthy" if all(r.is_healthy for r in results) else "unhealthy",
        "checks": [
            {"name": r.name, "status": "healthy" if r.is_healthy else "unhealthy"}
            for r in results
        ],
    }


@app.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    return {
        "requests": metrics.get_request_count(),
        "errors": metrics.get_error_count(),
        "avg_response_time": metrics.get_average_response_time(),
        "rps": metrics.get_requests_per_second(),
    }


@app.get("/stats")
async def get_stats():
    """Get application statistics"""
    return {
        "users": len(users_db),
        "products": len(products_db),
        "websocket_clients": len(websocket_clients),
        "cache_stats": cache_manager.get_stats(),
        "rate_limit_stats": rate_limiter.get_stats(),
    }


# Lifecycle events
@app.on_event("startup")
async def startup():
    """Application startup"""
    print("🚀 Complete QakeAPI Example starting...")


@app.on_event("shutdown")
async def shutdown():
    """Application shutdown"""
    print("🛑 Complete QakeAPI Example shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
