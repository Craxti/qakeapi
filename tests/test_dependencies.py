from typing import Any, Dict

import pytest
from qakeapi import QakeAPI, Request
from qakeapi.core.dependencies import DependencyResolver, Depends


async def get_config() -> Dict[str, Any]:
    """Dependency function that returns app configuration"""
    return {"app_name": "Test App", "version": "1.0.3"}


async def get_database() -> Dict[str, Any]:
    """Dependency function that returns database connection"""
    return {"connected": True, "instance_id": id(get_database)}


@pytest.fixture
def resolver():
    return DependencyResolver()


@pytest.fixture
def app():
    return QakeAPI()


@pytest.fixture
def mock_request():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [],
        "query_string": b"",
    }
    return Request(scope, lambda: None)


@pytest.mark.asyncio
async def test_dependency_resolution(mock_request):
    resolver = DependencyResolver()

    async def handler(config: Dict[str, Any] = Depends(get_config)):
        return config

    dependencies = await resolver.resolve_dependencies(handler, mock_request)
    result = await handler(**dependencies)
    assert result == {"app_name": "Test App", "version": "1.0.3"}


@pytest.mark.asyncio
async def test_multiple_dependencies(mock_request):
    resolver = DependencyResolver()

    async def handler(
        config: Dict[str, Any] = Depends(get_config),
        db: Dict[str, Any] = Depends(get_database),
    ):
        return {"config": config, "db": db}

    dependencies = await resolver.resolve_dependencies(handler, mock_request)
    result = await handler(**dependencies)
    assert result["config"] == {"app_name": "Test App", "version": "1.0.3"}
    assert result["db"]["connected"] is True


@pytest.mark.asyncio
async def test_dependency_caching(mock_request):
    resolver = DependencyResolver()

    async def handler(db1: Dict[str, Any] = Depends(get_database, use_cache=True)):
        return db1

    dependencies1 = await resolver.resolve_dependencies(handler, mock_request)
    result1 = await handler(**dependencies1)

    dependencies2 = await resolver.resolve_dependencies(handler, mock_request)
    result2 = await handler(**dependencies2)

    # Cached dependencies should return same instance
    assert result1["instance_id"] == result2["instance_id"]


def get_app_config():
    """Dependency that returns app configuration"""
    return {"app_name": "Test App", "version": "1.0.3"}
