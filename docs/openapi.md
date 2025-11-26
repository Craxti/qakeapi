# OpenAPI Documentation

QakeAPI automatically generates OpenAPI 3.0 specification and Swagger UI documentation.

## Automatic Generation

OpenAPI documentation is generated automatically:

```python
from qakeapi import QakeAPI

app = QakeAPI(
    title="My API",
    version="1.0.0",
    description="My awesome API documentation"
)

@app.get("/users/{id}")
def get_user(id: int):
    """Get user by ID."""
    return {"id": id, "name": "John"}

@app.post("/users")
async def create_user(request):
    """Create a new user."""
    data = await request.json()
    return {"id": 1, "data": data}
```

Access documentation:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Route Documentation

Document your routes with docstrings:

```python
@app.get("/users/{id}")
def get_user(id: int):
    """
    Get user by ID.
    
    Returns user information including name, email, and profile.
    """
    return {"id": id}

@app.post("/users")
async def create_user(request):
    """
    Create a new user.
    
    Requires:
    - name: User's full name
    - email: User's email address
    - age: User's age (optional)
    """
    data = await request.json()
    return {"id": 1}
```

## Parameter Documentation

Parameters are automatically documented:

```python
@app.get("/search")
def search(q: str, limit: int = 10, offset: int = 0):
    """
    Search endpoint.
    
    Args:
        q: Search query string
        limit: Maximum number of results (default: 10)
        offset: Number of results to skip (default: 0)
    """
    return {"results": []}
```

## Request Body Documentation

Request bodies are automatically inferred:

```python
class UserCreate:
    def __init__(self, name: str, email: str, age: int = None):
        self.name = name
        self.email = email
        self.age = age

@app.post("/users")
async def create_user(user: UserCreate):
    """Create user with automatic body extraction."""
    return {"id": 1}
```

## Response Documentation

Response types are automatically detected:

```python
from qakeapi.core.response import JSONResponse

@app.get("/users/{id}")
def get_user(id: int):
    """Get user by ID."""
    return JSONResponse({"id": id, "name": "John"})

@app.get("/error")
def error():
    """Return error response."""
    return {"error": "Not found"}, 404
```

## Custom OpenAPI Info

Customize OpenAPI information:

```python
app = QakeAPI(
    title="My API",
    version="1.0.0",
    description="Detailed API description",
    terms_of_service="https://example.com/terms",
    contact={
        "name": "API Support",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)
```

## Tags

Organize routes with tags:

```python
@app.get("/users", tags=["users"])
def get_users():
    return {"users": []}

@app.get("/posts", tags=["posts"])
def get_posts():
    return {"posts": []}
```

## Examples

Add examples to OpenAPI spec:

```python
@app.post("/users")
async def create_user(request):
    """
    Create user.
    
    Example request:
    {
        "name": "John Doe",
        "email": "john@example.com"
    }
    """
    data = await request.json()
    return {"id": 1}
```

## Best Practices

1. **Document all routes** - use docstrings for descriptions
2. **Use type hints** - helps with automatic schema generation
3. **Provide examples** - include example requests/responses
4. **Organize with tags** - group related endpoints
5. **Keep descriptions clear** - explain what each endpoint does


