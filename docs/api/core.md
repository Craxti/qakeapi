# Core API Reference

## Application

The main application class that handles routing and middleware.

```python
from qakeapi import QakeAPI

app = QakeAPI()
```

### Methods

#### route(path: str, methods: List[str] = None)

Register a route handler.

```python
@app.route("/path", methods=["GET"])
async def handler(request):
    return JSONResponse({"message": "Hello"})
```

#### add_middleware(middleware_class: Type[Middleware], **options)

Add middleware to the application.

```python
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

#### run(host: str = "0.0.0.0", port: int = 8000)

Run the application server.

```python
app.run(host="0.0.0.0", port=8000)
```

## Request

The request object containing information about the HTTP request.

### Properties

- `method`: HTTP method
- `path`: Request path
- `headers`: Request headers
- `query_params`: Query parameters
- `body`: Request body
- `json()`: Parse JSON body
- `form()`: Parse form data
- `client()`: Client information (IP, port)

## Response

Base response class and its variants.

### JSONResponse

```python
from qakeapi.core.responses import JSONResponse

response = JSONResponse(
    content={"message": "Success"},
    status_code=200
)
```

### Response Types

- `Response`: Base response class
- `JSONResponse`: JSON response
- `HTMLResponse`: HTML response
- `PlainTextResponse`: Text response
- `RedirectResponse`: Redirect response

## Router

Internal routing system.

```python
from qakeapi.core.routing import Router

router = Router()
router.add_route("/path", handler, methods=["GET"])
```

## Exceptions

Built-in exception classes.

```python
from qakeapi.core.exceptions import (
    HTTPException,
    NotFound,
    MethodNotAllowed,
    ValidationError
)

raise HTTPException(status_code=400, detail="Bad Request")
``` 