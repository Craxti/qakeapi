import asyncio

import pytest
from pytest_asyncio.plugin import event_loop_policy

from qakeapi.core.application import Application


@pytest.fixture
def app():
    """Fixture for creating test application"""
    return Application(
        title="Test API", version="1.0.3", description="Test API Description"
    )


@pytest.fixture(scope="session")
def event_loop_policy():
    """Create and set event loop policy for tests"""
    policy = asyncio.DefaultEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)
    return policy


@pytest.fixture
async def test_client(app):
    """Fixture for creating test client"""
    from httpx import AsyncClient

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
