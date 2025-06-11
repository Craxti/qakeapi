# QakeAPI

A lightweight Python web framework for building REST APIs with modern features like OpenAPI/Swagger documentation.

## Features

- Simple and intuitive routing system
- Automatic OpenAPI/Swagger documentation
- Request/Response model validation using Pydantic
- Built-in Swagger UI interface
- ASGI-compatible

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

1. Create a new file `app.py`:

```python
from qakeapi import Application, Request, Response
from pydantic import BaseModel

app = Application()

class EchoRequest(BaseModel):
    message: str

class EchoResponse(BaseModel):
    message: str

@app.post("/echo")
async def echo(request: Request) -> Response:
    data = await request.json()
    return Response(json={"message": data["message"]})

if __name__ == "__main__":
    app.run()
```

2. Run the application:

```bash
python app.py
```

3. Open http://localhost:8000/docs in your browser to see the Swagger UI documentation.

## License

MIT License 