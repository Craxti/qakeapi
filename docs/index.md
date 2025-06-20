# Welcome to QakeAPI

QakeAPI is a modern, fast, and secure API framework for Python, designed with simplicity and performance in mind.

## Features

- Fast and lightweight
- Built-in middleware support
- Security features (CORS, CSRF, Rate Limiting)
- Authentication support
- Easy to test and extend

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
async def hello_world():
    return JSONResponse({"message": "Hello, World!"})

if __name__ == "__main__":
    app.run() 