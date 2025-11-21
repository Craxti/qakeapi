"""
Tests for dependency injection system.
"""

import pytest
from qakeapi import Request, Depends
from qakeapi.core.dependencies import Dependency, resolve_dependencies


@pytest.mark.asyncio
async def test_simple_dependency():
    """Test simple dependency."""
    def get_user_id() -> int:
        return 123
    
    dependency = Depends(get_user_id)
    
    result = await dependency.resolve(None, {}, {})
    assert result == 123


@pytest.mark.asyncio
async def test_dependency_with_request():
    """Test dependency that uses Request."""
    def get_user_agent(request: Request) -> str:
        return request.get_header("user-agent", "unknown")
    
    dependency = Depends(get_user_agent)
    
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [(b"user-agent", b"test-agent")],
        "scheme": "http",
        "server": ("localhost", 8000),
    }
    
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    
    request = Request(scope, receive)
    
    result = await dependency.resolve(request, {}, {})
    assert result == "test-agent"


@pytest.mark.asyncio
async def test_dependency_with_params():
    """Test dependency with parameters."""
    def get_item(item_id: int, limit: int = 10) -> dict:
        return {"item_id": item_id, "limit": limit}
    
    dependency = Depends(get_item)
    
    path_params = {"item_id": "123"}
    query_params = {"limit": "20"}
    
    result = await dependency.resolve(None, path_params, query_params)
    assert result["item_id"] == 123  # converted to int
    assert result["limit"] == 20


@pytest.mark.asyncio
async def test_async_dependency():
    """Test async dependency."""
    async def get_data() -> dict:
        return {"data": "async"}
    
    dependency = Depends(get_data)
    
    result = await dependency.resolve(None, {}, {})
    assert result == {"data": "async"}


@pytest.mark.asyncio
async def test_dependency_caching():
    """Test dependency caching."""
    call_count = 0
    
    def get_counter() -> int:
        nonlocal call_count
        call_count += 1
        return call_count
    
    dependency = Depends(get_counter, use_cache=True)
    
    # First call
    result1 = await dependency.resolve(None, {}, {})
    assert result1 == 1
    assert call_count == 1
    
    # Second call - should use cache
    result2 = await dependency.resolve(None, {}, {})
    assert result2 == 1
    assert call_count == 1  # not incremented


@pytest.mark.asyncio
async def test_resolve_dependencies():
    """Test resolve_dependencies function."""
    def get_user_id() -> int:
        return 123
    
    def get_limit() -> int:
        return 10
    
    async def handler(request: Request, user_id: int = Depends(get_user_id), limit: int = Depends(get_limit)):
        return {"user_id": user_id, "limit": limit}
    
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "server": ("localhost", 8000),
    }
    
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    
    request = Request(scope, receive)
    
    dependencies = await resolve_dependencies(handler, request, {}, {})
    assert dependencies["user_id"] == 123
    assert dependencies["limit"] == 10
