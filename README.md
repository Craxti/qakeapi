# 🚀 QakeAPI 1.2.0

<div align="center">

**Revolutionary Hybrid Async/Sync Web Framework for Python**

> ⚡ The first framework with seamless sync/async support and reactive architecture

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/craxti/qakeapi)

</div>

---

## ✨ What Makes QakeAPI Unique?

**QakeAPI** is a completely new approach to web frameworks:

1. 🔄 **Hybrid Sync/Async** — write sync and async code simultaneously
2. ⚡ **Reactive Routing** — reactive routing and events
3. 🚀 **Parallel Dependencies** — automatic dependency parallelism
4. 🔗 **Pipeline Composition** — function composition into pipelines
5. 🎯 **Smart Routing** — intelligent routing based on conditions

### Key Features:

- ✅ **Zero Dependencies** — only Python standard library
- ✅ **Production-Ready** — ready for real-world projects
- ✅ **Performance** — automatic parallelism, optimized routing (Trie-based)
- ✅ **Simplicity** — intuitive syntax
- ✅ **Flexibility** — simultaneous sync and async support
- ✅ **OpenAPI/Swagger** — automatic API documentation
- ✅ **WebSocket Support** — real-time communication
- ✅ **Background Tasks** — asynchronous task processing
- ✅ **Middleware System** — customizable request/response processing
- ✅ **CORS Support** — built-in CORS middleware
- ✅ **Dependency Injection** — clean architecture with DI
- ✅ **Rate Limiting** — built-in rate limiting decorator
- ✅ **Caching** — response caching with TTL
- ✅ **Request Validation** — automatic data validation
- ✅ **File Upload** — multipart file upload with validation
- ✅ **Security** — request size limits, validation, error handling

---

## 🚀 Quick Start

### Installation

```bash
pip install qakeapi
```

### Simple Example

```python
from qakeapi import QakeAPI, CORSMiddleware

app = QakeAPI(
    title="My API",
    version="1.2.0",
    description="My awesome API"
)

# Add CORS middleware
app.add_middleware(CORSMiddleware(allow_origins=["*"]))

# Sync function works automatically!
@app.get("/users/{id}")
def get_user(id: int):
    return {"id": id, "name": f"User {id}"}

# Async function is also supported
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}

# POST with automatic body extraction
@app.post("/users")
async def create_user(request):
    data = await request.json()
    return {"message": "User created", "data": data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Access the API documentation:**
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## 📚 Core Features

### 1. Hybrid Sync/Async

Write synchronous code, the framework automatically handles it:

```python
@app.get("/users/{id}")
def get_user(id: int):  # Regular function!
    # Blocking operations automatically executed in executor
    user = database.get_user(id)
    posts = database.get_user_posts(id)
    return {"user": user, "posts": posts}
```

### 2. Parallel Dependencies

Dependencies execute in parallel:

```python
@app.get("/dashboard")
async def dashboard(
    user: User = get_user(),
    stats: Stats = get_stats(),
    notifications: list = get_notifications()
):
    # All three functions execute in parallel!
    return {
        "user": user,
        "stats": stats,
        "notifications": notifications
    }
```

### 3. Reactive Events

React to events in your application:

```python
@app.react("order:created")
async def on_order_created(event):
    order = event.data
    await inventory.reserve(order.items)
    await payment.process(order)
    await shipping.schedule(order)

# Emit event
await app.emit("order:created", order_data)
```

### 4. Pipeline Composition

Compose functions into pipelines:

```python
@app.pipeline([
    authenticate,
    authorize,
    validate,
    transform,
    save
])
def create_resource(data: ResourceData):
    return {"id": data.id, "status": "created"}
```

### 5. Smart Routing

Conditional routing based on conditions:

```python
@app.when(lambda req: req.headers.get("X-Client") == "mobile")
def mobile_handler(request):
    return {"mobile": True}

@app.when(lambda req: req.path.startswith("/api/v2"))
def v2_handler(request):
    return {"version": "2.0"}
```

### 6. Automatic API Documentation

OpenAPI/Swagger documentation is automatically generated:

```python
app = QakeAPI(
    title="My API",
    version="1.2.0",
    description="API documentation"
)

# All routes are automatically documented
@app.get("/users/{id}")
def get_user(id: int):
    """Get user by ID."""
    return {"id": id}
```

### 7. WebSocket Support

Real-time communication:

```python
@app.websocket("/ws/{room}")
async def websocket_handler(websocket: WebSocket, room: str):
    await websocket.accept()
    await websocket.send_json({"message": f"Welcome to {room}!"})
    
    async for message in websocket.iter_json():
        await websocket.send_json({"echo": message})
```

### 8. Background Tasks

Run tasks asynchronously:

```python
from qakeapi.core.background import add_background_task

@app.post("/process")
async def process_data(request):
    data = await request.json()
    
    # Run task in background
    await add_background_task(process_heavy_task, data)
    
    return {"message": "Processing started"}
```

### 9. Middleware System

Customize request/response processing:

```python
from qakeapi import CORSMiddleware, LoggingMiddleware, RequestSizeLimitMiddleware

app.add_middleware(CORSMiddleware(allow_origins=["*"]))
app.add_middleware(LoggingMiddleware())
app.add_middleware(RequestSizeLimitMiddleware(max_size=10 * 1024 * 1024))  # 10MB
```

### 10. Dependency Injection

Clean architecture with dependency injection:

```python
from qakeapi import QakeAPI, Depends

app = QakeAPI()

def get_database():
    return Database()

@app.get("/users")
async def get_users(db = Depends(get_database)):
    return await db.get_users()
```

### 11. Rate Limiting

Protect your API with rate limiting:

```python
from qakeapi import rate_limit

@rate_limit(requests_per_minute=60)
@app.get("/api/data")
def get_data():
    return {"data": "..."}
```

### 12. Response Caching

Cache responses for better performance:

```python
from qakeapi import cache

@cache(ttl=300)  # Cache for 5 minutes
@app.get("/expensive-operation")
def expensive_operation():
    return {"result": compute_expensive_result()}
```

### 13. File Upload

Handle file uploads with validation and security:

```python
from qakeapi import QakeAPI, FileUpload, IMAGE_TYPES

@app.post("/upload")
async def upload_image(file: FileUpload):
    # Validate file type
    if not file.validate_type(IMAGE_TYPES):
        return {"error": "Only images"}, 400
    
    # Validate size (5MB)
    if not file.validate_size(5 * 1024 * 1024):
        return {"error": "File too large"}, 400
    
    # Save file
    path = await file.save("uploads/")
    return {"path": path}
```

---

## 📦 Architecture

```
qakeapi/
├── core/              # Core components
│   ├── app.py        # Main QakeAPI class
│   ├── hybrid.py     # Hybrid executor (sync→async)
│   ├── router.py     # Smart router (Trie-optimized)
│   ├── reactive.py   # Reactive engine
│   ├── parallel.py   # Parallel resolver
│   ├── pipeline.py   # Pipeline processor
│   ├── request.py    # HTTP Request
│   ├── response.py   # HTTP Response
│   ├── middleware.py # Middleware system
│   ├── websocket.py  # WebSocket support
│   ├── background.py # Background tasks
│   ├── openapi.py    # OpenAPI generation
│   ├── files.py      # File upload handling
│   ├── dependencies.py # Dependency Injection
│   ├── validation.py # Data validation
│   ├── rate_limit.py # Rate limiting
│   ├── caching.py    # Response caching
│   ├── logging.py    # Logging system
│   └── exceptions.py # HTTP exceptions
└── utils/            # Utilities
```

---

## 📖 Documentation

Full documentation is available in the `docs/` directory:

- [Getting Started](docs/getting-started.md) - Quick start guide
- [File Upload](docs/file-upload.md) - File upload handling
- [Routing Guide](docs/routing.md) - Routing, handlers, and performance optimizations
- [Dependency Injection](docs/dependency-injection.md) - DI system for clean architecture
- [Reactive System](docs/reactive.md) - Event-driven architecture
- [Parallel Dependencies](docs/parallel.md) - Parallel dependency resolution
- [Pipelines](docs/pipelines.md) - Function pipelines
- [Middleware](docs/middleware.md) - Middleware system and security
- [WebSocket](docs/websocket.md) - WebSocket support
- [Background Tasks](docs/background-tasks.md) - Background processing
- [OpenAPI](docs/openapi.md) - API documentation
- [API Reference](docs/api-reference.md) - Complete API reference

---

## 🎯 Examples

Check out the `examples/` directory for complete examples:

- `basic_example.py` - Basic features demonstration
- `complete_example.py` - Full feature showcase
- `file_upload_example.py` - File upload handling
- `financial_calculator.py` - Complex real-world application

---

## 🔧 Requirements

- Python 3.9+
- uvicorn (optional, for running the server)

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

QakeAPI is built from scratch using only Python standard library,
demonstrating a new approach to web frameworks.

---

<div align="center">

**QakeAPI** - Build modern APIs with revolutionary approach! 🚀

Made with ❤️ by the QakeAPI team

</div>
