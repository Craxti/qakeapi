# Middleware System

QakeAPI includes a powerful middleware system for intercepting and processing requests and responses.

**Why QakeAPI middleware:** CORS, Logging, RequestSizeLimit built-in — no `starlette.middleware` or third-party packages. Simple `(request, next)` contract; each layer adds ~0.1–0.2ms. Benchmarks: 2 middleware layers → ~15K RPS vs ~11K FastAPI. See [benchmarks](benchmarks.md).

## Built-in Middleware

### CORS Middleware

Handle Cross-Origin Resource Sharing:

```python
from qakeapi import QakeAPI, CORSMiddleware

app = QakeAPI()

app.add_middleware(CORSMiddleware(
    allow_origins=["*"],  # Allow all origins
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"]   # Allow all headers
))

# Or specify specific origins
app.add_middleware(CORSMiddleware(
    allow_origins=["http://localhost:3000", "https://example.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"]
))
```

### Logging Middleware

Log all requests and responses:

```python
from qakeapi import QakeAPI, LoggingMiddleware

app = QakeAPI()
app.add_middleware(LoggingMiddleware())
```

### Request Size Limit Middleware

Validate request body size to prevent memory issues:

```python
from qakeapi import QakeAPI, RequestSizeLimitMiddleware

app = QakeAPI()

# Default: 10MB limit
app.add_middleware(RequestSizeLimitMiddleware())

# Custom size limit (5MB)
app.add_middleware(RequestSizeLimitMiddleware(max_size=5 * 1024 * 1024))

# Large file uploads (50MB)
app.add_middleware(RequestSizeLimitMiddleware(max_size=50 * 1024 * 1024))
```

This middleware:
- Checks `Content-Length` header before reading body
- Raises `PayloadTooLargeError` (HTTP 413) if limit exceeded
- Protects against memory exhaustion from large requests

## Custom Middleware

Create your own middleware:

```python
from qakeapi.core.middleware import BaseMiddleware

class AuthMiddleware(BaseMiddleware):
    async def process(self, request, call_next):
        # Check authentication
        token = request.headers.get("Authorization")
        if not token:
            from qakeapi.core.response import JSONResponse
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
        # Add user info to request
        request.user = decode_token(token)
        
        # Continue to next middleware or handler
        response = await call_next(request)
        
        # Modify response if needed
        response.headers["X-User-ID"] = str(request.user.id)
        
        return response

app.add_middleware(AuthMiddleware())
```

## Middleware Order

Middleware executes in the order it's added:

```python
# Execution order:
# 1. CORS middleware
# 2. Logging middleware
# 3. Auth middleware
# 4. Handler

app.add_middleware(CORSMiddleware())
app.add_middleware(LoggingMiddleware())
app.add_middleware(AuthMiddleware())
```

## Request Processing

Access and modify requests:

```python
class RequestModifierMiddleware(BaseMiddleware):
    async def process(self, request, call_next):
        # Modify request
        request.custom_header = "custom_value"
        
        # Add query parameter
        if "page" not in request.query_params:
            request.query_params["page"] = ["1"]
        
        response = await call_next(request)
        return response
```

## Response Processing

Modify responses:

```python
class ResponseModifierMiddleware(BaseMiddleware):
    async def process(self, request, call_next):
        response = await call_next(request)
        
        # Add custom header
        response.headers["X-Custom-Header"] = "value"
        
        # Modify status code
        if response.status_code == 200:
            response.headers["X-Success"] = "true"
        
        return response
```

## Error Handling

Handle errors in middleware:

```python
class ErrorHandlingMiddleware(BaseMiddleware):
    async def process(self, request, call_next):
        try:
            response = await call_next(request)
            return response
        except ValueError as e:
            from qakeapi.core.response import JSONResponse
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            from qakeapi.core.response import JSONResponse
            return JSONResponse({"error": "Internal error"}, status_code=500)
```

## Rate Limiting

QakeAPI provides built-in rate limiting via the `@rate_limit` decorator. See the [Rate Limiting Guide](../examples/rate_limit_example.py) for details.

For custom rate limiting middleware:

```python
from collections import defaultdict
from time import time

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, max_requests=100, window=60):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
    
    async def process(self, request, call_next):
        client_ip = request.headers.get("X-Forwarded-For", "unknown")
        now = time()
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.max_requests:
            from qakeapi.core.response import JSONResponse
            return JSONResponse(
                {"error": "Rate limit exceeded"},
                status_code=429
            )
        
        # Record request
        self.requests[client_ip].append(now)
        
        response = await call_next(request)
        return response

app.add_middleware(RateLimitMiddleware(max_requests=100, window=60))
```

## Best Practices

1. **Order matters** - add middleware in the order you want it to execute
2. **Keep middleware focused** - one responsibility per middleware
3. **Handle errors** - don't let middleware break the request chain
4. **Use async** - middleware should be async for I/O operations
5. **Document middleware** - explain what each middleware does


