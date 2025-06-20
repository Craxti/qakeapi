# Security API Reference

## CORS Configuration

Configure Cross-Origin Resource Sharing settings.

```python
from qakeapi.security.cors import CORSConfig

config = CORSConfig(
    allow_origins=["https://trusted-domain.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization"],
    allow_credentials=True,
    expose_headers=["X-Custom-Header"],
    max_age=3600
)
```

## CSRF Protection

Implement Cross-Site Request Forgery protection.

```python
from qakeapi.security.csrf import CSRFProtection

csrf = CSRFProtection(
    secret_key="your-secret-key",
    cookie_name="csrf_token",
    header_name="X-CSRF-Token"
)

# In your route handler
@app.route("/protected", methods=["POST"])
async def protected_route(request):
    await csrf.validate_token(request)
    # Your route logic here
```

## Token Validation

Validate JWT tokens.

```python
from qakeapi.security.jwt import (
    create_token,
    validate_token,
    decode_token
)

# Create a token
token = create_token(
    data={"user_id": 123},
    secret_key="your-secret-key",
    algorithm="HS256",
    expires_in=3600
)

# Validate a token
is_valid = validate_token(
    token,
    secret_key="your-secret-key",
    algorithms=["HS256"]
)

# Decode token data
payload = decode_token(
    token,
    secret_key="your-secret-key",
    algorithms=["HS256"]
)
```

## Password Hashing

Secure password hashing utilities.

```python
from qakeapi.security.password import (
    hash_password,
    verify_password
)

# Hash a password
hashed = hash_password("user_password")

# Verify a password
is_valid = verify_password("user_password", hashed)
```

## Security Headers

Add security headers to responses.

```python
from qakeapi.security.headers import SecurityHeaders

headers = SecurityHeaders(
    hsts=True,
    xss_protection=True,
    content_security_policy={
        "default-src": ["'self'"],
        "script-src": ["'self'", "trusted-scripts.com"]
    }
)

# In your middleware
response.headers.update(headers.get_headers())
```

## Rate Limiting Configuration

Configure rate limiting rules.

```python
from qakeapi.security.rate_limit import RateLimitConfig

config = RateLimitConfig(
    requests_per_minute=60,
    burst_size=10,
    storage_backend="memory",
    key_prefix="rate_limit:"
)
``` 