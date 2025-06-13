import asyncio

import pytest

from qakeapi.core.application import Application


@pytest.fixture
def app():
    """Фикстура для создания тестового приложения"""
    return Application(
        title="Test API", version="1.0.0", description="Test API Description"
    )


@pytest.fixture
def event_loop():
    """Создает новый event loop для каждого теста"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_client(app):
    """Фикстура для создания тестового клиента"""
    from httpx import AsyncClient

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
