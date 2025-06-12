# QakeAPI 🚀

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

QakeAPI is a modern, fast, and easy-to-use ASGI web framework for building APIs with Python. It's designed to be simple yet powerful, with built-in support for WebSockets, background tasks, authentication, and more.

## ✨ Features

- 🌟 **Modern Python** - Type hints, async/await support
- 🔒 **Built-in Authentication** - Basic auth and custom auth backends
- 🛡️ **Role-based Authorization** - Flexible permission system
- 📝 **Automatic API Documentation** - Swagger/OpenAPI integration
- 🔌 **WebSocket Support** - Full duplex communication
- 🎯 **Background Tasks** - Async task management
- 🧩 **Dependency Injection** - Clean and maintainable code
- 📊 **Validation** - Request/response validation with Pydantic

## 🚀 Quick Start

```bash
# Install the package
pip install qakeapi

# Create a basic app
from qakeapi.core.application import Application
from qakeapi.core.responses import Response

app = Application(
    title="Hello World",
    version="1.0.0"
)

@app.get("/")
async def hello(request):
    return Response.json({"message": "Hello, World!"})

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 📚 Examples

Check out the [examples](examples/) directory for more detailed examples:

- [Basic App](examples/basic_app.py) - Simple REST API
- [Auth App](examples/auth_app.py) - Authentication and authorization
- [WebSocket App](examples/websocket_app.py) - WebSocket communication
- [Background Tasks](examples/background_tasks_app.py) - Async task handling

## 🔧 Installation

```bash
pip install qakeapi
```

## 📖 Documentation

### Basic Usage

```python
from qakeapi.core.application import Application
from qakeapi.core.responses import Response
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

app = Application()

@app.post("/items")
async def create_item(request):
    data = await request.json()
    return Response.json({"item": data})
```

### WebSocket Support

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message received: {data}")
```

### Authentication

```python
from qakeapi.security.authentication import BasicAuthBackend
from qakeapi.security.authorization import requires_auth, IsAuthenticated

auth_backend = BasicAuthBackend()
auth_backend.add_user("admin", "password", ["admin"])

@app.get("/protected")
@requires_auth(IsAuthenticated())
async def protected_route(request):
    return Response.json({"message": "Access granted!"})
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - For inspiration
- [Starlette](https://www.starlette.io/) - For ASGI implementation ideas
- [Pydantic](https://pydantic-docs.helpmanual.io/) - For data validation

## 📬 Contact

If you have any questions or suggestions, feel free to open an issue or reach out to the maintainers.

---

Made with ❤️ by the QakeAPI team 