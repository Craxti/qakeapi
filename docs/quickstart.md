# Quick Start Guide

## Basic Application

Create a new file `app.py`:

```python
from qakeapi import QakeAPI
from qakeapi.core.responses import JSONResponse

app = QakeAPI()

@app.route("/")
async def hello_world():
    return JSONResponse({"message": "Hello, World!"})

@app.route("/items/{item_id}")
async def get_item(request, item_id: int):
    return JSONResponse({
        "item_id": item_id,
        "name": f"Item {item_id}"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## Running the Application

Run your application:

```bash
python app.py
```

Your API will be available at `http://localhost:8000`

## Adding Middleware

```python
from qakeapi.core.middleware import CORSMiddleware

app.add_middleware(CORSMiddleware, 
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"]
)
```

## Authentication

```python
from qakeapi.core.middleware import AuthenticationMiddleware

app.add_middleware(AuthenticationMiddleware,
    auth_scheme="Bearer",
    exempt_paths=["/login", "/public"]
)
```

## Rate Limiting

```python
from qakeapi.core.middleware import RateLimitMiddleware

app.add_middleware(RateLimitMiddleware,
    requests_per_minute=60
)
``` 