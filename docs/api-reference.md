# API Reference

Complete API reference for QakeAPI 1.2.0.

## QakeAPI Class

Main application class.

### Initialization

```python
app = QakeAPI(
    title: str = "QakeAPI",
    version: str = "1.2.0",
    description: str = None,
    debug: bool = False
)
```

### Route Registration

#### GET

```python
@app.get(
    path: str,
    condition: Callable = None,
    name: str = None
)
```

#### POST

```python
@app.post(
    path: str,
    condition: Callable = None,
    name: str = None
)
```

#### PUT

```python
@app.put(
    path: str,
    condition: Callable = None,
    name: str = None
)
```

#### DELETE

```python
@app.delete(
    path: str,
    condition: Callable = None,
    name: str = None
)
```

#### WebSocket

```python
@app.websocket(path: str)
```

### Event System

#### Emit Event

```python
await app.emit(event_name: str, data: Any)
```

#### React to Event

```python
@app.react(event_name: str)
async def handler(event):
    pass
```

### Middleware

```python
app.add_middleware(middleware: BaseMiddleware)
```

### Lifecycle

#### Startup

```python
@app.on_startup
def startup():
    pass
```

#### Shutdown

```python
@app.on_shutdown
def shutdown():
    pass
```

## File Upload

### FileUpload

Represents an uploaded file from multipart/form-data request.

```python
from qakeapi import FileUpload

@app.post("/upload")
async def upload_file(file: FileUpload):
    # File is automatically extracted from multipart request
    saved_path = await file.save("uploads/")
    return {"path": saved_path}
```

#### Properties

- `filename: str` - Original filename
- `content: bytes` - File content
- `content_type: str` - MIME type
- `size: int` - File size in bytes
- `extension: str` - File extension (without dot)
- `name: str` - File name without extension

#### Methods

- `read() -> bytes` - Read file content
- `read_text(encoding: str = "utf-8") -> str` - Read as text
- `save(destination: str, filename: Optional[str] = None) -> str` - Save to disk
- `save_to_temp(suffix: Optional[str] = None) -> str` - Save to temp file
- `validate_size(max_size: int) -> bool` - Validate file size
- `validate_type(allowed_types: Set[str]) -> bool` - Validate by extension
- `validate_content_type(allowed_types: Set[str]) -> bool` - Validate MIME type

#### Predefined Types

```python
from qakeapi import IMAGE_TYPES, DOCUMENT_TYPES, IMAGE_MIME_TYPES, DOCUMENT_MIME_TYPES

# Use in validation
if file.validate_type(IMAGE_TYPES):
    # It's an image
    pass
```

### Request File Methods

#### `request.files() -> Dict[str, FileUpload]`

Get all uploaded files from multipart request.

```python
files = await request.files()
file = files.get("myfile")
```

#### `request.form_and_files() -> Dict[str, Any]`

Get both form fields and files.

```python
data = await request.form_and_files()
fields = data["fields"]  # Dict[str, str]
files = data["files"]     # Dict[str, FileUpload]
```

## Request Object

HTTP request object.

### Properties

- `method: str` - HTTP method
- `path: str` - Request path
- `headers: Dict[str, str]` - Request headers
- `query_params: Dict[str, List[str]]` - Query parameters

### Methods

#### Get Query Parameter

```python
request.get_query_param(key: str, default: Any = None) -> Any
```

#### Get Body

```python
await request.body() -> bytes
```

#### Get JSON

```python
await request.json() -> Any
```

## Response Objects

### Response

Base response class.

```python
Response(
    content: Any = None,
    status_code: int = 200,
    headers: Dict[str, str] = None,
    media_type: str = None
)
```

### JSONResponse

JSON response.

```python
JSONResponse(
    content: Any,
    status_code: int = 200,
    headers: Dict[str, str] = None
)
```

### HTMLResponse

HTML response.

```python
HTMLResponse(
    content: str,
    status_code: int = 200,
    headers: Dict[str, str] = None
)
```

## Middleware

### BaseMiddleware

Base class for custom middleware.

```python
class MyMiddleware(BaseMiddleware):
    async def process(self, request, call_next):
        # Process request
        response = await call_next(request)
        # Process response
        return response
```

### CORSMiddleware

CORS middleware.

```python
CORSMiddleware(
    allow_origins: List[str] = None,
    allow_methods: List[str] = None,
    allow_headers: List[str] = None
)
```

### LoggingMiddleware

Logging middleware.

```python
LoggingMiddleware(logger=None)
```

### RequestSizeLimitMiddleware

Request size limit middleware.

```python
RequestSizeLimitMiddleware(max_size: int = 10 * 1024 * 1024)
```

Raises `PayloadTooLargeError` (HTTP 413) if request body exceeds limit.

## WebSocket

### WebSocket Object

```python
class WebSocket:
    async def accept(self)
    async def close(self, code: int = 1000)
    async def send_json(self, data: Any)
    async def send_text(self, text: str)
    async def send_bytes(self, data: bytes)
    async def iter_json(self)
    async def iter_text(self)
    async def iter_bytes(self)
```

## Background Tasks

### Add Background Task

```python
from qakeapi.core.background import add_background_task

await add_background_task(func, *args, **kwargs)
```

### Background Task Manager

```python
from qakeapi.core.background import BackgroundTaskManager

manager = BackgroundTaskManager()
task_id = await manager.add_task(func, *args, wait=False)
```

## Dependency Injection

### Depends

Dependency injection decorator.

```python
from qakeapi import Depends

def get_db():
    return Database()

@app.get("/users")
async def get_users(db = Depends(get_db)):
    return await db.get_users()
```

With caching:

```python
@app.get("/config")
async def get_config(config = Depends(get_config, cache=True)):
    return config
```

### Dependency

Dependency wrapper class.

```python
from qakeapi.core.dependencies import Dependency

dep = Dependency(func, cache=False)
result = await dep.resolve(**kwargs)
```

## Utilities

### Hybrid Executor

```python
from qakeapi.core.hybrid import run_hybrid

result = await run_hybrid(func, *args, **kwargs)
```

### Parallel Resolver

```python
from qakeapi.core.parallel import ParallelResolver

resolver = ParallelResolver()
results = await resolver.resolve_parallel([func1, func2, func3])
```

### Pipeline

```python
from qakeapi.core.pipeline import Pipeline

pipeline = Pipeline([step1, step2, step3])
result = await pipeline.execute(data)
```

## Error Handling

### HTTP Exceptions

QakeAPI provides HTTP exception classes:

```python
from qakeapi.core.exceptions import (
    HTTPException,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    InternalServerError,
    PayloadTooLargeError
)

@app.get("/users/{id}")
def get_user(id: int):
    if id < 0:
        raise ValidationError("Invalid user ID")
    
    user = database.get_user(id)
    if not user:
        raise NotFoundError("User not found")
    
    return user
```

### Return Error Response

```python
@app.get("/error")
def error():
    return {"error": "Not found"}, 404
```

### Exception Handling

```python
@app.get("/users/{id}")
def get_user(id: int):
    try:
        user = database.get_user(id)
        return user
    except UserNotFound:
        return {"error": "User not found"}, 404
```

## Type Conversion

Automatic type conversion for path and query parameters:

- `int` - Integer conversion
- `float` - Float conversion
- `bool` - Boolean conversion (true, 1, yes, on)
- `str` - String (default)

## Best Practices

1. Use type hints for automatic validation
2. Document routes with docstrings
3. Handle errors gracefully
4. Use async for I/O operations
5. Use sync for CPU-bound operations


