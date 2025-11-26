# Dependency Injection

QakeAPI includes a powerful dependency injection system that simplifies testing, code organization, and resource management.

## Basic Usage

Use the `Depends()` decorator to inject dependencies:

```python
from qakeapi import QakeAPI, Depends

app = QakeAPI()

def get_database():
    return Database()

@app.get("/users")
async def get_users(db = Depends(get_database)):
    return await db.get_users()
```

## How It Works

1. Dependencies are resolved automatically when the route handler is called
2. Dependencies can be sync or async functions
3. Dependencies receive context (request, path params, etc.) automatically
4. Dependencies are resolved in the order they appear in the function signature

## Dependency Caching

Cache expensive dependencies to avoid repeated computation:

```python
def load_config():
    """Expensive operation - load config from file."""
    return load_config_from_file()

@app.get("/settings")
async def get_settings(config = Depends(load_config, cache=True)):
    """Config is loaded once and cached."""
    return config

@app.get("/other-settings")
async def get_other_settings(config = Depends(load_config, cache=True)):
    """Uses cached config."""
    return config
```

## Request Context

Dependencies automatically receive request context:

```python
def get_current_user(request):
    """Extract user from request."""
    token = request.headers.get("Authorization")
    return decode_token(token)

@app.get("/profile")
async def get_profile(user = Depends(get_current_user)):
    return {"user": user}
```

## Path Parameters

Dependencies can access path parameters:

```python
def get_user_by_id(id: int):
    """Dependency receives path parameter."""
    return database.get_user(id)

@app.get("/users/{id}")
async def get_user(user = Depends(get_user_by_id)):
    """User is already loaded."""
    return user
```

## Nested Dependencies

Dependencies can depend on other dependencies:

```python
def get_database():
    return Database()

def get_user_service(db = Depends(get_database)):
    """Dependency depends on another dependency."""
    return UserService(db)

@app.get("/users/{id}")
async def get_user(service = Depends(get_user_service)):
    return await service.get_user(id)
```

## Testing with Dependencies

Dependencies make testing easier:

```python
# In tests, you can override dependencies
def mock_database():
    return MockDatabase()

# Override dependency
app.dependency_overrides[get_database] = mock_database

# Or use a test client with dependency overrides
```

## Common Patterns

### Database Connection

```python
def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()

@app.get("/users")
async def get_users(db = Depends(get_db)):
    return await db.get_users()
```

### Authentication

```python
def get_current_user(request):
    token = request.headers.get("Authorization")
    if not token:
        raise UnauthorizedError("Missing token")
    return decode_token(token)

@app.get("/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"user_id": user.id}
```

### Configuration

```python
def get_config():
    return load_config()

@app.get("/api/config")
async def get_api_config(config = Depends(get_config, cache=True)):
    return config
```

### Service Layer

```python
def get_user_service(db = Depends(get_database)):
    return UserService(db)

@app.get("/users/{id}")
async def get_user(id: int, service = Depends(get_user_service)):
    return await service.get_user(id)
```

## Best Practices

1. **Use dependency injection** for shared resources (database, config, services)
2. **Cache expensive dependencies** with `cache=True`
3. **Keep dependencies focused** - one responsibility per dependency
4. **Use type hints** for better IDE support and validation
5. **Document dependencies** with docstrings
6. **Test dependencies separately** from route handlers

## Advanced Usage

### Custom Dependency Class

```python
from qakeapi.core.dependencies import Dependency

class DatabaseDependency(Dependency):
    def __init__(self):
        super().__init__(get_database, cache=True)

@app.get("/users")
async def get_users(db = Depends(DatabaseDependency())):
    return await db.get_users()
```

### Dependency with Validation

```python
def get_user_id(request):
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise UnauthorizedError("Missing user ID")
    return int(user_id)

@app.get("/profile")
async def get_profile(user_id = Depends(get_user_id)):
    return {"user_id": user_id}
```

## Performance Considerations

- Dependencies are resolved once per request
- Cached dependencies (`cache=True`) are resolved once and reused
- Dependencies are resolved asynchronously for better performance
- Use caching for expensive operations (file I/O, database connections, etc.)

