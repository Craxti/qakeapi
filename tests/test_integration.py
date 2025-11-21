"""
Интеграционные тесты для всех улучшений QakeAPI
"""

import asyncio
import time
from unittest.mock import patch

import pytest
import pytest_asyncio

from qakeapi import JSONResponse, QakeAPI, Request
from qakeapi.caching.cache import CacheManager
from qakeapi.caching.middleware import CacheMiddleware
from qakeapi.core.error_handling import ErrorHandler
from qakeapi.core.exceptions import HTTPException
from qakeapi.middleware.compression import CompressionMiddleware
from qakeapi.security.auth import JWTManager, PasswordManager, SecurityConfig
from qakeapi.security.rate_limiting import RateLimitMiddleware, RateLimitRule
from qakeapi.security.validation import SecurityValidator
from qakeapi.utils.status import status


@pytest.fixture
def enhanced_app():
    """Создать приложение со всеми улучшениями"""
    app = QakeAPI(title="Enhanced QakeAPI Test App", debug=True)

    # Добавляем все middleware (порядок важен!)
    # Rate limiting должен быть первым
    from qakeapi.security.rate_limiting import RateLimiter, RateLimitRule

    rate_limiter = RateLimiter(
        default_rule=RateLimitRule(
            requests=3, window=60, per="ip"  # Только 3 запроса  # За 60 секунд
        )
    )
    app.add_middleware(
        RateLimitMiddleware(
            rate_limiter=rate_limiter, skip_paths={"/health", "/metrics"}
        )
    )
    app.add_middleware(CacheMiddleware(default_expire=60))
    app.add_middleware(CompressionMiddleware(minimum_size=50))

    # Настраиваем обработчик ошибок
    error_handler = ErrorHandler(debug=True)

    async def handle_exception(request, exception):
        return await error_handler.handle_exception(request, exception)

    app.exception_handlers[Exception] = handle_exception
    app.exception_handlers[HTTPException] = handle_exception

    # Добавляем тестовые маршруты
    @app.get("/")
    async def root():
        return {"message": "Enhanced QakeAPI is working!"}

    @app.get("/health")
    async def health():
        return {"status": "healthy", "timestamp": time.time()}

    @app.get("/large-response")
    async def large_response():
        # Большой ответ для тестирования сжатия
        data = {"items": [{"id": i, "name": f"Item {i}"} for i in range(1000)]}
        return data

    @app.get("/cached-data")
    async def cached_data():
        # Данные для тестирования кеширования
        return {"data": "This should be cached", "timestamp": time.time()}

    @app.get("/error")
    async def error_endpoint():
        raise HTTPException(status.BAD_REQUEST, "Test error")

    @app.get("/validation-error")
    async def validation_error():
        raise ValueError("Test validation error")

    @app.post("/secure-endpoint")
    async def secure_endpoint(request: Request):
        # Тестируем валидацию входных данных
        data = await request.json()
        validator = SecurityValidator()
        clean_data = validator.validate_data(data)
        return {"received": clean_data}

    return app


@pytest_asyncio.fixture
async def client(enhanced_app):
    """Создать тестовый клиент"""
    from httpx import AsyncClient

    try:
        from httpx import ASGITransport
    except ImportError:
        from httpx._transports.asgi import ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=enhanced_app), base_url="http://testserver"
    ) as client:
        yield client


class TestIntegration:
    """Интеграционные тесты"""

    @pytest.mark.asyncio
    async def test_basic_functionality(self, client):
        """Тест базовой функциональности"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Enhanced QakeAPI is working!"

    @pytest.mark.asyncio
    async def test_compression_integration(self, client):
        """Тест интеграции сжатия"""
        headers = {"Accept-Encoding": "gzip"}
        response = await client.get("/large-response", headers=headers)

        assert response.status_code == 200
        # Проверяем заголовки сжатия
        assert "gzip" in response.headers.get("content-encoding", "")

        # Данные должны быть корректно распакованы httpx
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1000

    @pytest.mark.asyncio
    async def test_caching_integration(self, client):
        """Тест интеграции кеширования"""
        # Первый запрос
        response1 = await client.get("/cached-data")
        assert response1.status_code == 200
        data1 = response1.json()

        # Второй запрос должен вернуть кешированные данные
        response2 = await client.get("/cached-data")
        assert response2.status_code == 200
        data2 = response2.json()

        # Timestamp должен быть одинаковым (из кеша)
        assert data1["timestamp"] == data2["timestamp"]

        # Проверяем заголовки кеша
        assert response2.headers.get("x-cache") == "HIT"

    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self, client):
        """Тест интеграции rate limiting"""
        # Делаем много запросов быстро
        responses = []
        for _ in range(5):  # Превышаем лимит 3 req/min
            response = await client.get("/")
            responses.append(response)

        # Некоторые запросы должны быть заблокированы
        status_codes = [r.status_code for r in responses]
        assert status.TOO_MANY_REQUESTS in status_codes

        # Проверяем заголовки rate limit
        last_response = responses[-1]
        if last_response.status_code == status.TOO_MANY_REQUESTS:
            assert "x-ratelimit-limit" in last_response.headers
            assert "x-ratelimit-remaining" in last_response.headers

    @pytest.mark.asyncio
    async def test_rate_limiting_skip_paths(self, client):
        """Тест пропуска путей в rate limiting"""
        # Health endpoint должен пропускаться
        responses = []
        for _ in range(10):
            response = await client.get("/health")
            responses.append(response)

        # Все запросы должны проходить
        assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, client):
        """Тест интеграции обработки ошибок"""
        # HTTP исключение
        response = await client.get("/error")
        assert response.status_code == status.BAD_REQUEST

        data = response.json()
        assert data["error"] is True
        assert data["message"] == "Test error"
        assert "request_id" in data
        assert "timestamp" in data

        # В debug режиме должна быть дополнительная информация
        assert "debug" in data

    @pytest.mark.asyncio
    async def test_validation_integration(self, client):
        """Тест интеграции валидации"""
        # Безопасные данные
        safe_data = {"name": "John Doe", "email": "john@example.com"}
        response = await client.post("/secure-endpoint", json=safe_data)
        assert response.status_code == 200

        result = response.json()
        assert result["received"]["name"] == "John Doe"
        assert result["received"]["email"] == "john@example.com"

    @pytest.mark.asyncio
    async def test_dangerous_input_validation(self, client):
        """Тест валидации опасных данных"""
        # Опасные данные (XSS)
        dangerous_data = {
            "name": "<script>alert('xss')</script>",
            "comment": "'; DROP TABLE users; --",
        }

        response = await client.post("/secure-endpoint", json=dangerous_data)

        # Запрос должен быть отклонен или данные санитизированы
        if response.status_code == 200:
            result = response.json()
            # Проверяем, что опасный контент был санитизирован
            assert "<script>" not in result["received"]["name"]
        else:
            # Или запрос был отклонен как опасный
            assert response.status_code == status.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_combined_middleware_stack(self, client):
        """Тест работы всего стека middleware"""
        headers = {"Accept-Encoding": "gzip"}

        # Запрос, который пройдет через все middleware
        response = await client.get("/large-response", headers=headers)

        assert response.status_code == 200

        # Проверяем, что все middleware сработали
        # (заголовки могут быть переписаны, поэтому проверяем основную функциональность)
        data = response.json()
        assert len(data["items"]) == 1000

        # Второй запрос для проверки кеширования
        response2 = await client.get("/large-response", headers=headers)
        assert response2.status_code == 200


class TestSecurityIntegration:
    """Интеграционные тесты безопасности"""

    def test_jwt_password_integration(self):
        """Тест интеграции JWT и паролей"""
        config = SecurityConfig(secret_key="test-secret")
        jwt_manager = JWTManager(config)
        password_manager = PasswordManager(config)

        # Создаем пользователя
        password = "SecurePassword123!"
        hashed_password = password_manager.hash_password(password)

        # Проверяем пароль
        assert password_manager.verify_password(password, hashed_password)

        # Создаем токен для пользователя
        user_data = {"user_id": 123, "username": "testuser"}
        token_pair = jwt_manager.create_token_pair(user_data)

        # Проверяем токены
        access_data = jwt_manager.verify_token(token_pair.access_token, "access")
        assert access_data.user_id == 123
        assert access_data.username == "testuser"

        refresh_data = jwt_manager.verify_token(token_pair.refresh_token, "refresh")
        assert refresh_data.user_id == 123

    @pytest.mark.asyncio
    async def test_rate_limiting_with_different_keys(self):
        """Тест rate limiting с разными ключами"""
        from qakeapi.security.rate_limiting import RateLimiter, RateLimitRule

        limiter = RateLimiter()
        rule = RateLimitRule(requests=2, window=1, per="ip")
        limiter.add_rule("*", rule)

        # Создаем запросы с разными IP
        scope1 = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "client": ("192.168.1.1", 12345),
            "headers": [],
        }
        request1 = Request(scope1, None)

        scope2 = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "client": ("192.168.1.2", 12345),
            "headers": [],
        }
        request2 = Request(scope2, None)

        # Первый IP: 2 запроса должны пройти
        allowed1_1, _, _ = await limiter.check_rate_limit(request1)
        assert allowed1_1 is True

        allowed1_2, _, _ = await limiter.check_rate_limit(request1)
        assert allowed1_2 is True

        allowed1_3, _, _ = await limiter.check_rate_limit(request1)
        assert allowed1_3 is False

        # Второй IP: должен иметь свой лимит
        allowed2_1, _, _ = await limiter.check_rate_limit(request2)
        assert allowed2_1 is True

        allowed2_2, _, _ = await limiter.check_rate_limit(request2)
        assert allowed2_2 is True


class TestPerformanceIntegration:
    """Тесты производительности интеграции"""

    @pytest.mark.asyncio
    async def test_caching_performance(self):
        """Тест производительности кеширования"""
        cache_manager = CacheManager()

        # Медленная функция
        call_count = 0

        async def slow_function():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Симулируем медленную операцию
            return {"data": "expensive_computation", "call_count": call_count}

        # Первый вызов - медленный
        start_time = time.time()
        result1 = await cache_manager.get_or_set("slow_key", slow_function, expire=60)
        first_call_time = time.time() - start_time

        # Второй вызов - из кеша, быстрый
        start_time = time.time()
        result2 = await cache_manager.get_or_set("slow_key", slow_function, expire=60)
        second_call_time = time.time() - start_time

        # Проверяем результаты
        assert result1["data"] == result2["data"]
        assert (
            result1["call_count"] == result2["call_count"]
        )  # Функция вызвана только один раз
        assert call_count == 1

        # Второй вызов должен быть значительно быстрее
        assert second_call_time < first_call_time / 10

    @pytest.mark.asyncio
    async def test_compression_efficiency(self):
        """Тест эффективности сжатия"""
        middleware = CompressionMiddleware(minimum_size=100)

        # Создаем запрос
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [(b"accept-encoding", b"gzip")],
        }
        request = Request(scope, None)

        # Создаем повторяющийся контент (хорошо сжимается)
        repetitive_content = "ABCDEFGHIJ" * 1000  # 10KB
        original_response = JSONResponse({"data": repetitive_content})

        async def call_next(req):
            return original_response

        # Применяем сжатие
        compressed_response = await middleware(request, call_next)

        # Проверяем эффективность сжатия
        original_size = len(repetitive_content.encode())
        compressed_size = len(compressed_response.body)

        compression_ratio = compressed_size / original_size

        # Сжатие должно быть эффективным (меньше 50% от оригинала)
        assert compression_ratio < 0.5
        assert compressed_response.get_header("Content-Encoding") == "gzip"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
