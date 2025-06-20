# Middleware API Reference

## Base Middleware

All middleware classes inherit from the base `Middleware` class.

```python
from qakeapi.core.middleware import Middleware

class CustomMiddleware(Middleware):
    async def __call__(self, request, call_next):
        return await call_next(request)
```

## CORSMiddleware

Configure Cross-Origin Resource Sharing.

```python
from qakeapi.core.middleware import CORSMiddleware

CORSMiddleware(
    allow_origins: List[str] = ["*"],
    allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers: List[str] = ["*"],
    allow_credentials: bool = False,
    expose_headers: List[str] = None,
    max_age: int = 600
)
```

## AuthenticationMiddleware

Handle request authentication.

```python
from qakeapi.core.middleware import AuthenticationMiddleware

AuthenticationMiddleware(
    auth_scheme: str = "Bearer",
    exempt_paths: List[str] = None,
    token_validator: Callable[[str], bool] = None
)
```

## RateLimitMiddleware

Implement rate limiting.

```python
from qakeapi.core.middleware import RateLimitMiddleware

RateLimitMiddleware(
    requests_per_minute: int = 60,
    window_size: int = 60,
    exempt_paths: List[str] = None
)
```

## RequestLoggingMiddleware

Log request information.

```python
from qakeapi.core.middleware import RequestLoggingMiddleware

RequestLoggingMiddleware(
    log_format: str = None,
    logger: Logger = None
)
```

## ErrorHandlingMiddleware

Handle exceptions and convert them to responses.

```python
from qakeapi.core.middleware import ErrorHandlingMiddleware

ErrorHandlingMiddleware(
    handlers: Dict[Type[Exception], Callable] = None
)
```

## Middleware Stack

Example of combining multiple middleware:

```python
from qakeapi import QakeAPI
from qakeapi.core.middleware import (
    CORSMiddleware,
    AuthenticationMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware
)

app = QakeAPI()

# Order matters - first added = outer layer
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.add_middleware(AuthenticationMiddleware, auth_scheme="Bearer")
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
``` 