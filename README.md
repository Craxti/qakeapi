# QakeAPI Framework

A lightweight ASGI-based web framework for building fast and secure APIs in Python.

## Features

- ASGI-compatible web framework
- Built-in authentication and authorization
- Request/Response handling
- Middleware support
- WebSocket support
- Pydantic integration for data validation
- API documentation generation

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/qakeapi.git
cd qakeapi
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the example application:
```bash
python examples/auth_app.py
```

## Example Usage

```python
from qakeapi import Application
from qakeapi.core.responses import Response

app = Application()

@app.get("/")
async def hello(request):
    return Response.json({"message": "Hello, World!"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Authentication Example

The framework includes built-in authentication support. Here's a basic example:

```python
from qakeapi.security.authentication import BasicAuthBackend
from qakeapi.security.authorization import requires_auth, IsAuthenticated

auth_backend = BasicAuthBackend()
auth_backend.add_user("user", "password123", ["user"])

@app.get("/profile")
@requires_auth(IsAuthenticated())
async def profile(request):
    return Response.json({
        "username": request.user.username,
        "roles": request.user.roles
    })
```

## License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - For inspiration
- [Starlette](https://www.starlette.io/) - For ASGI implementation ideas
- [Pydantic](https://pydantic-docs.helpmanual.io/) - For data validation

## 📬 Contact

If you have any questions or suggestions, feel free to open an issue or reach out to the maintainers.

---

Made with ❤️ by the QakeAPI team 