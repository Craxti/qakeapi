# QakeAPI

QakeAPI is a modern, fast (high-performance) ASGI web framework for building APIs with Python 3.8+.

## Key Features

- **Fast**: High performance, on par with NodeJS and Go
- **Intuitive**: Great editor support. Completion everywhere. Less time debugging.
- **Easy**: Designed to be easy to use and learn. Less time reading docs.
- **Short**: Minimize code duplication. Multiple features from each parameter declaration.
- **Robust**: Get production-ready code. With automatic interactive documentation.
- **Standards-based**: Based on (and fully compatible with) OpenAPI (formerly known as Swagger) and JSON Schema.

## Requirements

Python 3.8+

## Installation

```bash
pip install qakeapi
```

## Example

```python
from qakeapi import Application

app = Application()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

## Documentation Structure

- **Getting Started**: Basic installation and usage
- **User Guide**: Detailed explanation of core concepts
- **API Reference**: Complete API documentation
- **Advanced Topics**: Performance optimization and best practices
- **Development**: Contributing guidelines and project information 