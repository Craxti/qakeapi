import time

import pytest

from qakeapi.core.request import Request
from qakeapi.core.responses import Response
from qakeapi.security.rate_limit import (
    InMemoryRateLimiter,
    RateLimitInfo,
    RateLimitMiddleware,
)


@pytest.fixture
def rate_limiter():
    return InMemoryRateLimiter(requests_per_minute=2)


@pytest.mark.asyncio
async def test_rate_limiter_allowed(rate_limiter):
    # Первый запрос должен быть разрешен
    allowed, info = await rate_limiter.is_allowed("test_key")
    assert allowed is True
    assert info.remaining == 1  # Учитываем текущий запрос
    assert info.limit == 2

    # Обновляем состояние после запроса
    await rate_limiter.update("test_key")

    # Второй запрос тоже должен быть разрешен
    allowed, info = await rate_limiter.is_allowed("test_key")
    assert allowed is True
    assert info.remaining == 0  # После первого запроса и учитывая текущий

    # Обновляем состояние после запроса
    await rate_limiter.update("test_key")

    # Третий запрос должен быть отклонен
    allowed, info = await rate_limiter.is_allowed("test_key")
    assert allowed is False
    assert info.remaining == 0


@pytest.mark.asyncio
async def test_rate_limit_reset(rate_limiter):
    # Делаем два запроса
    await rate_limiter.is_allowed("test_key")
    await rate_limiter.update("test_key")
    await rate_limiter.is_allowed("test_key")
    await rate_limiter.update("test_key")

    # Изменяем время для симуляции прошедшей минуты
    rate_limiter.storage["test_key"] = {time.time() - 61: 1, time.time() - 61: 1}

    # После сброса лимита запрос должен быть разрешен
    allowed, info = await rate_limiter.is_allowed("test_key")
    assert allowed is True
    assert info.remaining == 1  # Учитываем текущий запрос


@pytest.mark.asyncio
async def test_rate_limit_middleware():
    rate_limiter = InMemoryRateLimiter(requests_per_minute=2)
    middleware = RateLimitMiddleware(rate_limiter)

    # Создаем тестовый запрос
    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/test",
            "client": ("127.0.0.1", 8000),
        }
    )

    # Тестовый обработчик
    async def handler(request):
        return Response.text("OK", headers={})

    # Первый запрос должен пройти
    response = await middleware(request, handler)
    assert response.status_code == 200
    headers_dict = dict((k.decode(), v.decode()) for k, v in response.headers)
    assert headers_dict["X-RateLimit-Remaining"] == "1"

    # Второй запрос должен пройти
    response = await middleware(request, handler)
    assert response.status_code == 200
    headers_dict = dict((k.decode(), v.decode()) for k, v in response.headers)
    assert headers_dict["X-RateLimit-Remaining"] == "0"

    # Третий запрос должен быть отклонен
    response = await middleware(request, handler)
    assert response.status_code == 429
    headers_dict = dict((k.decode(), v.decode()) for k, v in response.headers)
    assert headers_dict["X-RateLimit-Remaining"] == "0"


@pytest.mark.asyncio
async def test_custom_key_function():
    rate_limiter = InMemoryRateLimiter(requests_per_minute=2)
    # Используем пользовательскую функцию для ключа
    middleware = RateLimitMiddleware(
        rate_limiter,
        key_func=lambda request: dict(request.headers)
        .get(b"x-api-key", b"default")
        .decode(),
    )

    # Создаем два запроса с разными API ключами
    request1 = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/test",
            "client": ("127.0.0.1", 8000),
            "headers": [(b"x-api-key", b"key1")],
        }
    )

    request2 = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/test",
            "client": ("127.0.0.1", 8000),
            "headers": [(b"x-api-key", b"key2")],
        }
    )

    async def handler(request):
        return Response.text("OK", headers={})

    # Запросы с разными ключами должны иметь отдельные лимиты
    response1 = await middleware(request1, handler)
    assert response1.status_code == 200

    response2 = await middleware(request2, handler)
    assert response2.status_code == 200

    # Второй запрос для первого ключа
    response1 = await middleware(request1, handler)
    assert response1.status_code == 200

    # Третий запрос для первого ключа должен быть отклонен
    response1 = await middleware(request1, handler)
    assert response1.status_code == 429

    # Второй запрос для второго ключа должен пройти
    response2 = await middleware(request2, handler)
    assert response2.status_code == 200
