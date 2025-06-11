# QakeAPI

QakeAPI is a lightweight ASGI web framework for building fast web APIs with Python, inspired by FastAPI.

## Features

- FastAPI-like route decorators
- ASGI compatibility
- Automatic OpenAPI/Swagger documentation
- Path parameters support
- JSON request/response handling
- Form data and file upload support
- Cookie handling
- Middleware support
- Type hints

## Installation

```bash
pip install qakeapi
```

## Quick Start

```python
from qakeapi.core.application import Application
from qakeapi.core.responses import Response
from qakeapi.core.requests import Request

app = Application(
    title="Basic Example",
    version="1.0.0",
    description="A basic example of QakeAPI application"
)

@app.get("/")
async def index(request: Request):
    return Response.json({
        "message": "Welcome to QakeAPI!"
    })

@app.get("/hello/{name}")
async def hello(request: Request, name: str):
    return Response.text(f"Hello, {name}!")

@app.post("/echo")
async def echo(request: Request):
    data = await request.json()
    return Response.json(data)
```

Run the application:

```bash
uvicorn your_app:app --reload
```

Visit http://localhost:8000/docs to see the automatic API documentation.

## License

MIT License 