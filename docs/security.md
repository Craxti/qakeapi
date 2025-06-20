# Security

QakeAPI provides several security features to help protect your application.

## CORS Protection

Configure Cross-Origin Resource Sharing to protect against unauthorized domain access:

```python
from qakeapi.core.middleware import CORSMiddleware

app.add_middleware(CORSMiddleware,
    allow_origins=["https://trusted-domain.com"],
    allow_methods=["GET", "POST"],
    allow_credentials=True,
    allow_headers=["Authorization"]
)
```

## Authentication

Implement token-based authentication:

```python
from qakeapi.core.middleware import AuthenticationMiddleware
import jwt

def validate_token(token: str) -> bool:
    try:
        jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        return True
    except jwt.InvalidTokenError:
        return False

app.add_middleware(AuthenticationMiddleware,
    auth_scheme="Bearer",
    token_validator=validate_token
)
```

## Rate Limiting

Protect against DDoS attacks and abuse:

```python
from qakeapi.core.middleware import RateLimitMiddleware

app.add_middleware(RateLimitMiddleware,
    requests_per_minute=60,
    window_size=60
)
```

## Best Practices

1. Always use HTTPS in production
2. Implement proper authentication and authorization
3. Validate and sanitize all input
4. Use secure headers
5. Keep dependencies up to date
6. Implement proper error handling
7. Use rate limiting
8. Enable CORS only for trusted domains
9. Use secure session handling
10. Implement logging and monitoring

## Example Secure Configuration

```python
from qakeapi import QakeAPI
from qakeapi.core.middleware import (
    CORSMiddleware,
    AuthenticationMiddleware,
    RateLimitMiddleware
)

app = QakeAPI()

# Security middleware stack
app.add_middleware(CORSMiddleware,
    allow_origins=["https://trusted-domain.com"],
    allow_credentials=True
)

app.add_middleware(AuthenticationMiddleware,
    auth_scheme="Bearer",
    exempt_paths=["/login"]
)

app.add_middleware(RateLimitMiddleware,
    requests_per_minute=60
)

# Secure routes
@app.route("/api/secure", methods=["POST"])
async def secure_endpoint(request):
    # Your secure endpoint logic here
    pass
``` 