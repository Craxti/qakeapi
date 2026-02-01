# Parallel Dependencies

QakeAPI automatically resolves dependencies in parallel, improving performance for independent operations.

**Why QakeAPI parallel deps win:** Independent dependencies (no cross-deps) run via `asyncio.gather()`. Three 10ms DB/API calls → 10ms total, not 30ms. FastAPI does the same, but QakeAPI has less overhead (no Pydantic model injection). Benchmarks: ~8.4K RPS vs ~6.2K FastAPI for 3-dependency endpoints. See [benchmarks](benchmarks.md).

## Basic Usage

Dependencies are automatically resolved in parallel:

```python
from qakeapi import QakeAPI

app = QakeAPI()

def get_user():
    # Simulate database call
    return {"id": 1, "name": "John"}

def get_stats():
    # Simulate API call
    return {"views": 100, "likes": 50}

def get_notifications():
    # Simulate cache lookup
    return [{"id": 1, "message": "New message"}]

@app.get("/dashboard")
async def dashboard(
    user = get_user(),
    stats = get_stats(),
    notifications = get_notifications()
):
    """
    All three dependencies execute in parallel!
    Total time = max(get_user, get_stats, get_notifications)
    Instead of sum of all three.
    """
    return {
        "user": user,
        "stats": stats,
        "notifications": notifications
    }
```

## How It Works

When QakeAPI detects multiple dependencies, it:

1. **Identifies independent dependencies** - functions that don't depend on each other
2. **Executes them in parallel** - using asyncio for async functions or thread pool for sync
3. **Waits for all to complete** - then passes results to the handler

## Async Dependencies

Async dependencies are executed concurrently:

```python
async def fetch_user_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/user")
        return response.json()

async def fetch_user_posts():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/posts")
        return response.json()

@app.get("/profile")
async def profile(
    user_data = fetch_user_data(),
    posts = fetch_user_posts()
):
    """Both API calls happen in parallel."""
    return {
        "user": user_data,
        "posts": posts
    }
```

## Sync Dependencies

Sync dependencies are executed in thread pool:

```python
def calculate_statistics():
    # CPU-intensive calculation
    return {"total": 1000, "average": 50}

def fetch_from_cache():
    # Cache lookup
    return {"cached_data": "value"}

@app.get("/analytics")
async def analytics(
    stats = calculate_statistics(),
    cache = fetch_from_cache()
):
    """Both execute in parallel in thread pool."""
    return {"stats": stats, "cache": cache}
```

## Mixed Dependencies

Mix async and sync dependencies:

```python
async def fetch_from_api():
    # Async API call
    return await api.get_data()

def calculate_value():
    # Sync calculation
    return 42

@app.get("/data")
async def get_data(
    api_data = fetch_from_api(),
    calculated = calculate_value()
):
    """Async and sync execute in parallel."""
    return {"api": api_data, "calculated": calculated}
```

## Dependent Dependencies

Dependencies that depend on each other are resolved sequentially:

```python
def get_user_id():
    return 1

def get_user_data(user_id):
    # This depends on get_user_id result
    return {"id": user_id, "name": "John"}

@app.get("/user")
async def user(
    user_id = get_user_id(),
    user_data = get_user_data(user_id)  # Depends on user_id
):
    """user_id resolves first, then user_data."""
    return user_data
```

## Performance Benefits

### Sequential (Traditional)

```python
# Total time: 100ms + 150ms + 200ms = 450ms
user = get_user()        # 100ms
stats = get_stats()      # 150ms
notifications = get_notifications()  # 200ms
```

### Parallel (QakeAPI)

```python
# Total time: max(100ms, 150ms, 200ms) = 200ms
# 55% faster!
@app.get("/dashboard")
async def dashboard(
    user = get_user(),           # 100ms
    stats = get_stats(),         # 150ms
    notifications = get_notifications()  # 200ms
):
    # All execute in parallel
    pass
```

## Best Practices

1. **Use for independent operations** - parallel execution only helps if operations are independent
2. **Avoid side effects** - dependencies should be pure functions when possible
3. **Use async for I/O** - async dependencies are more efficient for I/O operations
4. **Document dependencies** - make it clear what each dependency does
5. **Handle errors** - dependencies can fail, handle errors appropriately

## Limitations

- Dependencies must be callable (functions or callable objects)
- Circular dependencies are not supported
- Dependencies with complex interdependencies may not parallelize optimally


