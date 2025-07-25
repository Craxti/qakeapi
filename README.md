# QakeAPI 🚀

A modern, lightweight, and fast ASGI web framework for building APIs in Python, focusing on developer experience and performance.

[![Tests](https://github.com/Craxti/qakeapi/actions/workflows/tests.yml/badge.svg)](https://github.com/Craxti/qakeapi/actions/workflows/tests.yml)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![PyPI version](https://badge.fury.io/py/qakeapi.svg)](https://badge.fury.io/py/qakeapi)
[![Downloads](https://pepy.tech/badge/qakeapi)](https://pepy.tech/project/qakeapi)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen)](https://qakeapi.readthedocs.io/)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)](https://codecov.io/gh/Craxti/qakeapi)

<p align="center">
  <img src="logo.png" alt="QakeAPI Logo" width="200"/>
</p>

## 📖 Table of Contents

- [✨ Why QakeAPI?](#-why-qakeapi)
- [🎯 Perfect For](#-perfect-for)
- [🏗️ Architecture Overview](#️-architecture-overview)
- [🚀 Quick Start](#-quick-start)
- [🛠️ CLI Tool](#️-cli-tool)
- [🌟 Key Features](#-key-features)
- [📚 Documentation](#-documentation)
- [🔥 Live Demos](#-live-demos)
- [🔧 How-To Guides](#-how-to-guides)
- [🔥 Real-World Examples](#-real-world-examples)
- [🤝 Contributing](#-contributing)
- [📬 Get in Touch](#-get-in-touch)

## ✨ Why QakeAPI?

- 🚀 **High Performance**: Built on ASGI for maximum speed and scalability
- 💡 **Intuitive API**: Clean, Pythonic interface that feels natural
- 📝 **Auto Documentation**: OpenAPI/Swagger docs generated automatically
- 🔒 **Security First**: Built-in authentication, CORS, and rate limiting
- 🎯 **Type Safety**: Full type hints support for better IDE integration
- 📦 **Modular**: Easy to extend with middleware and plugins
- 🔄 **Event-Driven**: Built-in event bus and saga pattern support
- 🌐 **WebSocket Ready**: Native WebSocket support with clustering
- 📊 **GraphQL Support**: Integrated GraphQL with Ariadne
- 🔄 **API Versioning**: Multiple versioning strategies (path, header, query)

## 🎯 Perfect For

- RESTful APIs
- Microservices
- Real-time applications
- API Gateways
- Backend for SPAs
- Serverless Functions
- WebSocket applications
- GraphQL APIs
- Event-driven systems

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    QakeAPI Framework                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Routing   │  │ Middleware  │  │ Validation  │        │
│  │             │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Security   │  │  Templates  │  │   Testing   │        │
│  │             │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ WebSockets  │  │   GraphQL   │  │    Events   │        │
│  │             │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Versioning  │  │  Clustering │  │   Caching   │        │
│  │             │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Request Flow

```
Client Request
     ↓
┌─────────────────┐
│   Middleware    │ ← CORS, Auth, Rate Limiting
└─────────────────┘
     ↓
┌─────────────────┐
│    Routing      │ ← Path matching, versioning
└─────────────────┘
     ↓
┌─────────────────┐
│  Validation     │ ← Pydantic models, type checking
└─────────────────┘
     ↓
┌─────────────────┐
│   Handler       │ ← Your business logic
└─────────────────┘
     ↓
┌─────────────────┐
│   Response      │ ← JSON, templates, files
└─────────────────┘
     ↓
Client Response
```

## 🚀 Quick Start

### Option 1: Using CLI (Recommended)

```bash
# Install QakeAPI
pip install qakeapi

# Create a new project with CLI
python3 qakeapi_cli.py create my-api --template=api

# Navigate to project and run
cd my-api
python app/main.py
```

### Option 2: Manual Setup

```bash
pip install qakeapi
```

Create a simple API in seconds:

```python
from qakeapi import Application, Response
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

app = Application()

@app.get("/")
async def hello():
    return {"message": "Hello, World!"}

@app.post("/items")
async def create_item(item: Item):
    return Response.json(item.dict(), status_code=201)

if __name__ == "__main__":
    app.run()
```

### Option 3: Advanced Example with All Features

```python
from qakeapi import Application, Response
from qakeapi.security import requires_auth, JWTAuthBackend
from qakeapi.middleware import CORSMiddleware
from qakeapi.security import RateLimiter
from pydantic import BaseModel
from typing import List

class User(BaseModel):
    id: int
    name: str
    email: str

class UserCreate(BaseModel):
    name: str
    email: str

# Initialize app with middleware
app = Application()

# Add security middleware
auth = JWTAuthBackend(secret_key="your-secret-key")
cors = CORSMiddleware(allow_origins=["http://localhost:3000"])
rate_limiter = RateLimiter(requests_per_minute=60)

app.add_middleware(cors)
app.add_middleware(rate_limiter)

# Mock database
users_db = []

@app.get("/")
async def hello():
    return {"message": "Welcome to QakeAPI!", "version": "1.1.0"}

@app.get("/users", response_model=List[User])
async def get_users():
    return users_db

@app.post("/users", response_model=User)
async def create_user(user: UserCreate):
    new_user = User(id=len(users_db) + 1, **user.dict())
    users_db.append(new_user)
    return Response.json(new_user.dict(), status_code=201)

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    for user in users_db:
        if user.id == user_id:
            return user
    return Response.json({"error": "User not found"}, status_code=404)

@app.get("/protected")
@requires_auth(auth)
async def protected_route():
    return {"message": "This is a protected route!"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## 🛠️ CLI Tool

QakeAPI comes with a powerful CLI tool for rapid project scaffolding:

```bash
# List available templates and features
python3 qakeapi_cli.py list

# Create projects with different templates
python3 qakeapi_cli.py create my-api --template=api
python3 qakeapi_cli.py create my-web --template=web --features=auth,templates
python3 qakeapi_cli.py create my-microservice --template=microservice

# Interactive mode
python3 qakeapi_cli.py create my-app
```

**Available Templates:**
- **Basic API** - Simple CRUD operations
- **Full API** - Complete API with auth, database, cache
- **Web Application** - Templates, static files, frontend
- **Microservice** - Lightweight service with minimal dependencies

**Available Features:**
- Authentication (JWT)
- Database integration (SQLAlchemy)
- Caching (Redis)
- Rate limiting
- Templates (Jinja2)
- WebSockets
- Testing (pytest)
- Docker support
- Live reload for development

## 🌟 Key Features

### 🔐 Authentication & Security

```python
from qakeapi.security import requires_auth, JWTAuthBackend, BasicAuthBackend

# JWT Authentication
jwt_auth = JWTAuthBackend(secret_key="your-secret-key")

# Basic Authentication
basic_auth = BasicAuthBackend(users={"admin": "password"})

@app.get("/protected")
@requires_auth(jwt_auth)
async def protected():
    return {"message": "Secret data"}

@app.get("/admin")
@requires_auth(basic_auth)
async def admin():
    return {"message": "Admin only"}
```

### 🚦 Rate Limiting

```python
from qakeapi.security import RateLimiter

# Global rate limiting
limiter = RateLimiter(requests_per_minute=60)
app.add_middleware(limiter)

# Per-endpoint rate limiting
@app.get("/api/data")
@limiter.limit(requests_per_minute=10)
async def get_data():
    return {"data": "sensitive information"}
```

### 🌐 CORS Support

```python
from qakeapi.middleware import CORSMiddleware

cors = CORSMiddleware(
    allow_origins=["http://localhost:3000", "https://myapp.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True
)
app.add_middleware(cors)
```

### 🔄 WebSocket Support

```python
from qakeapi.core.websockets import WebSocketHandler

ws_handler = WebSocketHandler()

@ws_handler.on_connect
async def handle_connect(websocket):
    await websocket.send_json({"type": "welcome", "message": "Connected!"})

@ws_handler.on_message
async def handle_message(websocket, message):
    await websocket.send_json({"type": "echo", "data": message})

@app.websocket("/ws")
async def websocket_endpoint(websocket):
    await ws_handler.handle_connection(websocket)
```

### 📊 GraphQL Integration

```python
from qakeapi.api.graphql import QakeGraphQL
from ariadne import QueryType, make_executable_schema

# Define GraphQL schema
type_defs = """
  type Query {
    hello: String!
    users: [User!]!
  }
  
  type User {
    id: ID!
    name: String!
    email: String!
  }
"""

query = QueryType()

@query.field("hello")
def resolve_hello(*_):
    return "Hello from GraphQL!"

@query.field("users")
def resolve_users(*_):
    return [{"id": "1", "name": "John", "email": "john@example.com"}]

schema = make_executable_schema(type_defs, query)
graphql_app = QakeGraphQL(schema, debug=True)

# Mount GraphQL app
app.mount("/graphql", graphql_app)
```

### 🔄 Event-Driven Architecture

```python
from qakeapi.core.events import EventBus, Event

event_bus = EventBus()

@event_bus.subscribe("user.created")
async def handle_user_created(event: Event):
    print(f"New user created: {event.data}")

@app.post("/users")
async def create_user(user: UserCreate):
    new_user = User(id=1, **user.dict())
    
    # Publish event
    await event_bus.publish("user.created", new_user.dict())
    
    return new_user
```

### 📈 API Versioning

```python
from qakeapi.api.versioning import APIVersionManager, version_required

version_manager = APIVersionManager()

# Register version info
version_manager.register_version("v1", "2023-01-01", "Initial version")
version_manager.register_version("v2", "2023-06-01", "Enhanced features")

@app.get("/api/v1/users")
@version_required("v1")
async def get_users_v1():
    return {"users": [], "version": "v1"}

@app.get("/api/v2/users")
@version_required("v2")
async def get_users_v2(page: int = 1, limit: int = 10):
    return {
        "users": [],
        "pagination": {"page": page, "limit": limit},
        "version": "v2"
    }
```

## 📚 Documentation

- [📖 Quick Start Guide](docs/quickstart.rst)
- [🔧 API Reference](docs/api-reference.rst)
- [🛠️ Middleware Guide](docs/middleware.rst)
- [🔒 Security Best Practices](docs/security.rst)
- [🚀 Deployment Guide](docs/deployment.rst)
- [🧪 Testing Guide](docs/testing.rst)
- [📊 GraphQL Guide](docs/graphql.rst)
- [🔄 WebSocket Guide](docs/websockets.rst)
- [📈 API Versioning Guide](docs/versioning.rst)

## 🔥 Live Demos

Try our live examples:

- 🌐 **Basic API**: [http://localhost:8000](http://localhost:8000) (run `python examples_app/basic_crud_app.py`)
- 🔐 **Authentication**: [http://localhost:8001](http://localhost:8001) (run `python examples_app/auth_app.py`)
- 🔄 **WebSocket Chat**: [http://localhost:8002](http://localhost:8002) (run `python examples_app/websocket_app.py`)
- 📊 **GraphQL Playground**: [http://localhost:8003/graphql](http://localhost:8003/graphql) (run `python examples_app/graphql_app.py`)
- 📈 **API Versioning**: [http://localhost:8004](http://localhost:8004) (run `python examples_app/api_versioning_enhanced_app.py`)

**Start all demos at once:**
```bash
cd examples_app
python start_all_apps.py
```

## 🔧 How-To Guides

### How to Add Middleware

```python
from qakeapi import Application
from qakeapi.middleware import CORSMiddleware
from qakeapi.security import RateLimiter

app = Application()

# Add middleware in order (first added = first executed)
app.add_middleware(CORSMiddleware(allow_origins=["*"]))
app.add_middleware(RateLimiter(requests_per_minute=60))

# Custom middleware
class CustomMiddleware:
    async def __call__(self, request, handler):
        # Pre-processing
        print(f"Request to: {request.path}")
        
        # Call next handler
        response = await handler(request)
        
        # Post-processing
        response.headers["X-Custom"] = "QakeAPI"
        return response

app.add_middleware(CustomMiddleware())
```

### How to Implement Custom Event Handlers

```python
from qakeapi.core.events import EventHandler, Event, EventBus
from typing import Dict, Any

class EmailEventHandler(EventHandler):
    def __init__(self):
        self.event_names = {"user.created", "user.updated"}
    
    async def handle(self, event: Event) -> None:
        if event.name == "user.created":
            await self.send_welcome_email(event.data)
        elif event.name == "user.updated":
            await self.send_update_notification(event.data)
    
    async def send_welcome_email(self, user_data: Dict[str, Any]):
        print(f"Sending welcome email to {user_data['email']}")
    
    async def send_update_notification(self, user_data: Dict[str, Any]):
        print(f"Sending update notification to {user_data['email']}")

# Register with event bus
event_bus = EventBus()
event_bus.register_handler(EmailEventHandler())
```

### How to Test WebSocket Applications

```python
import pytest
import asyncio
from qakeapi.testing import TestClient
from examples_app.websocket_app import app

@pytest.mark.asyncio
async def test_websocket_connection():
    client = TestClient(app)
    
    # Connect to WebSocket
    async with client.websocket_connect("/ws") as websocket:
        # Send message
        await websocket.send_json({"type": "message", "text": "Hello"})
        
        # Receive response
        response = await websocket.receive_json()
        assert response["type"] == "echo"
        assert response["data"]["text"] == "Hello"

@pytest.mark.asyncio
async def test_websocket_authentication():
    client = TestClient(app)
    
    # Get auth token
    response = await client.post("/api/generate-token", json={"user_id": "123"})
    token = response.json()["token"]
    
    # Connect with token
    async with client.websocket_connect(f"/ws?token={token}") as websocket:
        # Should receive welcome message
        welcome = await websocket.receive_json()
        assert welcome["type"] == "welcome"
```

### How to Use API Versioning

```python
from qakeapi.api.versioning import APIVersionManager, version_required, deprecated_version

version_manager = APIVersionManager()

# Register versions
version_manager.register_version(
    "v1", 
    "2023-01-01", 
    "Initial API version",
    breaking_changes=[],
    new_features=["Basic CRUD operations"],
    bug_fixes=[]
)

version_manager.register_version(
    "v2", 
    "2023-06-01", 
    "Enhanced API with pagination",
    breaking_changes=["Response format changed"],
    new_features=["Pagination", "Filtering"],
    bug_fixes=["Fixed date parsing issue"]
)

# Mark v1 as deprecated
@app.get("/api/v1/users")
@deprecated_version("v1", "2024-01-01", "Use v2 instead")
async def get_users_v1():
    return {"users": [], "version": "v1"}

# New v2 endpoint
@app.get("/api/v2/users")
@version_required("v2")
async def get_users_v2(page: int = 1, limit: int = 10):
    return {
        "users": [],
        "pagination": {"page": page, "limit": limit},
        "version": "v2"
    }
```

## 🔥 Real-World Examples

Check out our [examples](examples_app/) directory for production-ready examples:

### 🚀 Quick Examples

```bash
# Start all examples
cd examples_app
python start_all_apps.py

# Run tests for all examples
python run_all_tests.py
```

### 📁 Example Applications

- [🔐 Authentication API](examples_app/auth_app.py) - JWT authentication with protected routes
- [🚦 Rate Limited API](examples_app/rate_limit_app.py) - Rate limiting with Redis
- [🌐 CORS-enabled API](examples_app/cors_app.py) - Cross-origin resource sharing
- [💬 WebSocket Chat](examples_app/websocket_app.py) - Real-time chat application
- [🔄 Background Tasks](examples_app/background_tasks_app.py) - Async task processing
- [📊 GraphQL API](examples_app/graphql_app.py) - GraphQL with Ariadne
- [🔐 Enhanced Security](examples_app/security_examples_app.py) - XSS, CSRF, SQL injection protection
- [📈 API Versioning](examples_app/api_versioning_enhanced_app.py) - Multiple versioning strategies
- [🔄 Event-Driven App](examples_app/event_driven_app.py) - Event bus and saga patterns
- [🌐 WebSocket Clustering](examples_app/websocket_clustered_app.py) - Multi-server WebSocket support

### 🧪 Testing Examples

- [Advanced Testing](examples_app/advanced_testing_app.py) - Comprehensive testing strategies
- [Performance Testing](examples_app/performance_examples_app.py) - Load testing and profiling
- [Enhanced Testing](examples_app/enhanced_testing_example.py) - Mocking and fixtures

## 🤝 Contributing

We love your input! We want to make contributing to QakeAPI as easy and transparent as possible. Check out our [Contributing Guide](CONTRIBUTING.md) to get started.

### Development Setup

```bash
git clone https://github.com/Craxti/qakeapi.git
cd qakeapi
pip install -e ".[dev]"
pytest
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=qakeapi --cov-report=html

# Run specific test file
pytest tests/test_websocket_auth.py -v

# Run examples and test endpoints
cd examples_app
python start_all_apps.py
python run_all_tests.py
```

### Code Quality

```bash
# Format code
black qakeapi/ tests/ examples_app/

# Lint code
flake8 qakeapi/ tests/ examples_app/

# Type checking
mypy qakeapi/
```

## 🌟 Show Your Support

Give a ⭐️ if this project helped you! Every star helps increase the visibility of the project.

## 📝 License

[MIT License](LICENSE) - feel free to use this project for your applications.

## 🙏 Acknowledgments

- Inspired by modern web frameworks like FastAPI and Starlette
- Built with love for the Python community
- Thanks to all our contributors!

## 📬 Get in Touch

- Report bugs by [creating an issue](https://github.com/Craxti/qakeapi/issues)
- Follow [@qakeapi](https://twitter.com/qakeapi) for updates
- Join our [Discord community](https://discord.gg/qakeapi)

---

<p align="center">Made with ❤️ by the QakeAPI Team</p> 