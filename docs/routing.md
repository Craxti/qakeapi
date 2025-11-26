# Routing Guide

QakeAPI provides flexible routing with support for path parameters, query parameters, and automatic body extraction.

## Basic Routing

### HTTP Methods

```python
from qakeapi import QakeAPI

app = QakeAPI()

@app.get("/users")
def get_users():
    return {"users": []}

@app.post("/users")
async def create_user(request):
    data = await request.json()
    return {"message": "Created", "data": data}

@app.put("/users/{id}")
async def update_user(id: int, request):
    data = await request.json()
    return {"id": id, "data": data}

@app.delete("/users/{id}")
def delete_user(id: int):
    return {"message": f"Deleted {id}"}
```

## Path Parameters

Extract parameters from the URL path:

```python
@app.get("/users/{id}")
def get_user(id: int):
    """Type conversion is automatic."""
    return {"id": id}

@app.get("/posts/{post_id}/comments/{comment_id}")
def get_comment(post_id: int, comment_id: int):
    return {"post_id": post_id, "comment_id": comment_id}
```

## Query Parameters

Access query parameters:

```python
@app.get("/search")
def search(q: str, limit: int = 10, offset: int = 0):
    """Query parameters with defaults."""
    return {
        "query": q,
        "limit": limit,
        "offset": offset
    }
```

Or access via request object:

```python
@app.get("/search")
def search(request):
    q = request.get_query_param("q")
    limit = int(request.get_query_param("limit", default="10"))
    return {"query": q, "limit": limit}
```

## Request Body

Automatic body extraction for POST, PUT, PATCH:

```python
@app.post("/users")
async def create_user(request):
    """Access body via request object."""
    data = await request.json()
    return {"created": data}

# Or use automatic extraction with models
class UserCreate:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

@app.post("/users")
async def create_user(user: UserCreate):
    """Body automatically extracted and converted."""
    return {"name": user.name, "email": user.email}
```

## Conditional Routing

Route based on request conditions:

```python
@app.when(lambda req: req.headers.get("X-Client") == "mobile")
def mobile_handler(request):
    return {"client": "mobile"}

@app.when(lambda req: req.path.startswith("/api/v2"))
def v2_handler(request):
    return {"version": "2.0"}
```

## Route Names

Name your routes for easy reference:

```python
@app.get("/users/{id}", name="get_user")
def get_user(id: int):
    return {"id": id}
```

## Response Status Codes

Return custom status codes:

```python
@app.post("/users")
async def create_user(request):
    data = await request.json()
    # Return tuple (data, status_code)
    return {"id": 1, "name": data["name"]}, 201

@app.get("/not-found")
def not_found():
    return {"error": "Not found"}, 404
```

## Error Handling

Handle errors in routes:

```python
@app.get("/users/{id}")
def get_user(id: int):
    if id < 0:
        return {"error": "Invalid ID"}, 400
    
    try:
        user = database.get_user(id)
        return user
    except UserNotFound:
        return {"error": "User not found"}, 404
```

## Routing Performance

QakeAPI uses an optimized routing system with Trie-based lookup for static routes:

- **Static routes** (without parameters) are matched in O(m) time where m is the path length
- **Dynamic routes** (with parameters like `/users/{id}`) use regex matching
- Routes are automatically categorized for optimal performance
- No changes needed in your code - optimization is transparent

Example:

```python
# Static route - fast Trie lookup
@app.get("/api/users")
def get_users():
    return {"users": []}

# Dynamic route - regex matching
@app.get("/api/users/{id}")
def get_user(id: int):
    return {"id": id}
```

## Dependency Injection

Use dependency injection to simplify testing and code organization:

```python
from qakeapi import QakeAPI, Depends

app = QakeAPI()

def get_database():
    return Database()

def get_current_user(request):
    token = request.headers.get("Authorization")
    return decode_token(token)

@app.get("/users/{id}")
async def get_user(id: int, db = Depends(get_database), user = Depends(get_current_user)):
    return await db.get_user(id, user_id=user.id)

# With caching (dependency resolved once and cached)
def get_config():
    return load_config()

@app.get("/settings")
async def get_settings(config = Depends(get_config, cache=True)):
    return config
```

Benefits:
- **Testability** - easy to mock dependencies
- **Reusability** - share dependencies across routes
- **Clean architecture** - separation of concerns
- **Caching** - cache expensive dependency resolutions

## Best Practices

1. **Use type hints** for automatic validation and conversion
2. **Use async** for I/O operations
3. **Use sync** for CPU-bound operations (automatically parallelized)
4. **Return appropriate status codes**
5. **Document your routes** with docstrings (appears in Swagger UI)
6. **Use Dependency Injection** for shared resources (database, config, etc.)
7. **Prefer static routes** when possible for better performance


