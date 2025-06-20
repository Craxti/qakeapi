# Welcome to QakeAPI

QakeAPI is a modern Python web framework designed for building fast, secure and scalable web applications.

## Features

- Fast and lightweight
- Built-in security features (CSRF, CORS, Rate Limiting)
- Extensive middleware support
- Authentication and authorization
- Easy to test and maintain

## Installation

```bash
pip install qakeapi
```

## Quick Example

```python
from qakeapi import QakeAPI
from qakeapi.core.responses import JSONResponse

app = QakeAPI()

@app.route("/")
async def hello_world(request):
    return JSONResponse({"message": "Hello, World!"})

if __name__ == "__main__":
    app.run()
```

## Project Status

Current test coverage: 93%

## Contributing

We welcome contributions! Please see our [Contributing Guide](contributing.md) for details. 