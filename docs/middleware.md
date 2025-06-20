# Middleware

QakeAPI provides several built-in middleware components for common functionality.

## CORS Middleware

Cross-Origin Resource Sharing (CORS) middleware allows you to control which domains can access your API.

```python
from qakeapi.core.middleware import CORSMiddleware

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True
)
```

## Authentication Middleware

Handle authentication for your API endpoints.

```python
from qakeapi.core.middleware import AuthenticationMiddleware

app.add_middleware(AuthenticationMiddleware,
    auth_scheme="Bearer",
    exempt_paths=["/login", "/public"],
    token_validator=your_token_validator_function
)
```

## Rate Limiting

Protect your API from abuse by limiting request rates.

```python
from qakeapi.core.middleware import RateLimitMiddleware

app.add_middleware(RateLimitMiddleware,
    requests_per_minute=60,
    window_size=60,
    exempt_paths=["/status"]
)
```

## Request Logging

Log incoming requests for monitoring and debugging.

```python
from qakeapi.core.middleware import RequestLoggingMiddleware

app.add_middleware(RequestLoggingMiddleware)
```

## Error Handling

Centralized error handling for your application.

```python
from qakeapi.core.middleware import ErrorHandlingMiddleware

app.add_middleware(ErrorHandlingMiddleware)
```

## Custom Middleware

Create your own middleware by inheriting from the base Middleware class:

```python
from qakeapi.core.middleware import Middleware

class CustomMiddleware(Middleware):
    async def __call__(self, request, call_next):
        # Pre-processing
        print("Before request")
        
        response = await call_next(request)
        
        # Post-processing
        print("After request")
        
        return response

app.add_middleware(CustomMiddleware)
``` 