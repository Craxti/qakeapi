# QakeAPI Tests

This directory contains unit tests for the QakeAPI framework.

## Test Structure

- `test_hybrid.py` - Tests for Hybrid Executor (sync/async conversion)
- `test_router.py` - Tests for Router and Route matching
- `test_request_response.py` - Tests for Request and Response classes
- `test_middleware.py` - Tests for Middleware system
- `test_websocket.py` - Tests for WebSocket support
- `test_background.py` - Tests for Background Tasks
- `test_reactive.py` - Tests for Reactive Events
- `test_openapi.py` - Tests for OpenAPI generation
- `test_app.py` - Integration tests for application

## Running Tests

### Installing Dependencies

```bash
pip install -e ".[test]"
# or
pip install pytest pytest-asyncio pytest-cov
```

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=qakeapi --cov-report=html
```

### Run Specific File

```bash
pytest tests/test_hybrid.py
```

### Run Specific Test

```bash
pytest tests/test_hybrid.py::TestHybridExecutor::test_sync_function_execution
```

### Run with Verbose Output

```bash
pytest -v
```

## Test Structure

Each test file contains:
- Test classes (`Test*`)
- Test methods (`test_*`)
- Fixtures for common data (`conftest.py`)

## Examples

### Test Sync Function

```python
def test_sync_function_execution(self):
    @hybrid_executor
    def sync_func(x: int, y: int) -> int:
        return x + y
    
    result = asyncio.run(sync_func(1, 2))
    assert result == 3
```

### Test Async Function

```python
@pytest.mark.asyncio
async def test_async_function_execution(self):
    @hybrid_executor
    async def async_func(x: int, y: int) -> int:
        await asyncio.sleep(0.001)
        return x + y
    
    result = await async_func(1, 2)
    assert result == 3
```

### Test with Fixtures

```python
@pytest.mark.asyncio
async def test_simple_get_route(self, app, scope, receive, send):
    @app.get("/test")
    def handler():
        return {"message": "test"}
    
    scope["path"] = "/test"
    await app(scope, receive, send)
    
    assert len(send.messages) >= 1
```

## Code Coverage

Goal - cover all main components:
- ✅ Hybrid Executor
- ✅ Router
- ✅ Request/Response
- ✅ Middleware
- ✅ WebSocket
- ✅ Background Tasks
- ✅ Reactive Events
- ✅ OpenAPI
- ✅ App (integration tests)
