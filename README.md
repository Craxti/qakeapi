# 🚀 QakeAPI

<div align="center">

**Modern asynchronous web framework for Python**

> ⚡ Built from scratch using only Python standard library

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/qakeapi/qakeapi)

</div>

---

## ✨ Features

- **⚡ High Performance**: Asynchronous request processing
- **🔧 Built from Scratch**: All methods implemented independently
- **📦 Minimal Dependencies**: Uses only Python standard library
- **🔒 Built-in Security**: Authentication, authorization, CORS, CSRF, rate limiting
- **📚 Automatic Documentation**: OpenAPI (Swagger) documentation generation
- **🔌 WebSocket Support**: Full WebSocket connection support
- **💉 Dependency Injection**: Powerful dependency injection system
- **🛠️ Middleware System**: Flexible middleware system
- **📝 Data Validation**: Automatic data validation
- **🔄 Full Async/Await**: Complete async/await support
- **📊 Monitoring**: Built-in metrics and health checks
- **💾 Caching**: In-memory caching support

---

## 🎯 Philosophy

**QakeAPI** is built with the philosophy that all core functionality should be implemented independently, using only Python's standard library. This ensures:

- **No External Dependencies**: Core framework has zero dependencies
- **Full Control**: Complete understanding and control over all code
- **Lightweight**: Minimal overhead and fast performance
- **Educational**: Learn how web frameworks work from the ground up

---

## 📦 Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/qakeapi/qakeapi.git
cd qakeapi

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Dependencies

**Required:**
- Python 3.9+

**Optional (for running server):**
```bash
pip install uvicorn
```

**For development:**
```bash
pip install -e ".[dev]"
```

The framework itself has **zero external dependencies** - all core functionality uses only Python's standard library!

---

## 🚀 Quick Start

Create a file `main.py`:

```python
from qakeapi import QakeAPI

app = QakeAPI(title="My First API")

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/items/{item_id}")
async def get_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run the server:
```bash
python main.py
```

Open your browser at http://localhost:8000 - you'll see a JSON response.

---

## 📚 Examples

### Basic Usage

```python
from qakeapi import QakeAPI

app = QakeAPI(title="My API")

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/items/{item_id}")
async def get_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}
```

### Validation

```python
from qakeapi import QakeAPI
from qakeapi.validation import BaseModel, Field

app = QakeAPI()

class UserCreate(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    email: str = Field(regex=r"^[^@]+@[^@]+\.[^@]+$")
    age: int = Field(min_value=18, max_value=120)

@app.post("/users")
async def create_user(user: UserCreate):
    return {"user": user.dict()}
```

### Dependency Injection

```python
from qakeapi import QakeAPI, Depends

app = QakeAPI()

async def get_database():
    return {"connected": True}

@app.get("/")
async def root(db: dict = Depends(get_database)):
    return {"database": db}
```

### WebSocket

```python
from qakeapi import QakeAPI, WebSocket

app = QakeAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"message": "Hello!"})
    
    async for message in websocket.iter_json():
        await websocket.send_json({"echo": message})
```

### Security

```python
from qakeapi import QakeAPI
from qakeapi.security import AuthManager, CORSMiddleware

app = QakeAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

auth_manager = AuthManager(secret_key="your-secret-key")

@app.post("/login")
async def login(request: Request):
    data = await request.json()
    token = auth_manager.create_access_token({"user_id": 1})
    return {"access_token": token}
```

See the `examples/` directory for more complete examples.

---

## 🏗️ Architecture

QakeAPI follows a modular architecture:

- **Core**: Application, Request, Response, Router, Middleware, WebSocket
- **Validation**: Data validators and models
- **Security**: Authentication, authorization, CORS, CSRF, rate limiting
- **Caching**: In-memory caching
- **Monitoring**: Metrics and health checks
- **Utils**: Static files, templates, JSON utilities
- **Testing**: Test client and helpers

See [ARCHITECTURE_PLAN.md](ARCHITECTURE_PLAN.md) for detailed architecture documentation.

---

## 📋 Development Status

**Current Status**: Alpha - Core features implemented

See [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) for the complete development roadmap.

### ✅ Completed
- ✅ Project structure and development environment
- ✅ Core framework (Request, Response, Router, Application, Middleware)
- ✅ Validation system (validators and models)
- ✅ Dependency Injection
- ✅ WebSocket support
- ✅ Security features (JWT, password hashing, CORS, CSRF, Rate Limiting)
- ✅ Caching (in-memory cache with TTL)
- ✅ OpenAPI documentation generation
- ✅ Static files and templates support

### 🚧 In Progress
- 🚧 Additional examples and documentation

### ⏳ Planned
- ⏳ Performance optimizations
- ⏳ Additional middleware
- ⏳ Enhanced template features

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=qakeapi --cov-report=html

# Run specific test file
pytest tests/test_core.py
```

---

## 📚 Documentation

- [Architecture Plan](ARCHITECTURE_PLAN.md) - Detailed architecture documentation
- [Development Plan](DEVELOPMENT_PLAN.md) - Complete development roadmap
- [API Reference](docs/API_REFERENCE.md) - Complete API reference
- [Guide](docs/GUIDE.md) - Comprehensive usage guide

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

QakeAPI is built from scratch as an educational project to understand how web frameworks work at a fundamental level.

---

<div align="center">

**QakeAPI** - Build modern APIs from scratch! 🚀

Made with ❤️ by the QakeAPI team

</div>
