"""
Тесты системы кеширования
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock

# Импортируем только необходимые модули без полного qakeapi
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from qakeapi.caching.cache import InMemoryCache, CacheManager, CacheEntry
from qakeapi.caching.middleware import CacheMiddleware
from qakeapi.core.request import Request
from qakeapi.core.response import JSONResponse


class TestInMemoryCache:
    """Тесты in-memory кеша"""
    
    @pytest.mark.asyncio
    async def test_basic_operations(self):
        """Тест базовых операций кеша"""
        cache = InMemoryCache()
        
        # Установка и получение значения
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"
        
        # Проверка существования
        exists = await cache.exists("key1")
        assert exists is True
        
        # Удаление
        deleted = await cache.delete("key1")
        assert deleted is True
        
        # Проверка после удаления
        result = await cache.get("key1")
        assert result is None
        
        exists = await cache.exists("key1")
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_expiration(self):
        """Тест истечения срока действия"""
        cache = InMemoryCache()
        
        # Устанавливаем значение с коротким TTL
        await cache.set("key1", "value1", expire=1)
        
        # Сразу должно быть доступно
        result = await cache.get("key1")
        assert result == "value1"
        
        # После истечения TTL должно исчезнуть
        await asyncio.sleep(1.1)
        result = await cache.get("key1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Тест вытеснения по LRU"""
        cache = InMemoryCache(max_size=2)
        
        # Заполняем кеш
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        # Небольшая задержка для различия времени
        await asyncio.sleep(0.01)
        
        # Обращаемся к первому ключу (обновляем время доступа)
        await cache.get("key1")
        
        # Небольшая задержка
        await asyncio.sleep(0.01)
        
        # Добавляем третий ключ (должен вытеснить key2)
        await cache.set("key3", "value3")
        
        # key1 должен остаться, key2 должен быть вытеснен
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") is None
        assert await cache.get("key3") == "value3"
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Тест очистки истекших записей"""
        cache = InMemoryCache()
        
        # Добавляем записи с разными TTL
        await cache.set("key1", "value1", expire=1)
        await cache.set("key2", "value2", expire=2)
        await cache.set("key3", "value3")  # Без TTL
        
        # Ждем истечения первого ключа
        await asyncio.sleep(1.1)
        
        # Очищаем истекшие записи
        cleaned = await cache.cleanup_expired()
        assert cleaned == 1
        
        # Проверяем состояние
        assert await cache.get("key1") is None
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"


class TestCacheManager:
    """Тесты менеджера кеша"""
    
    @pytest.mark.asyncio
    async def test_cache_manager_operations(self):
        """Тест операций менеджера кеша"""
        cache = CacheManager()
        
        # Тестируем get_or_set с синхронной функцией
        def factory():
            return "computed_value"
        
        result = await cache.get_or_set("key1", factory)
        assert result == "computed_value"
        
        # Второй вызов должен вернуть кешированное значение
        def factory2():
            return "new_value"
        
        result = await cache.get_or_set("key1", factory2)
        assert result == "computed_value"  # Из кеша
    
    @pytest.mark.asyncio
    async def test_cache_manager_async_factory(self):
        """Тест с асинхронной фабричной функцией"""
        cache = CacheManager()
        
        async def async_factory():
            await asyncio.sleep(0.01)
            return "async_value"
        
        result = await cache.get_or_set("key1", async_factory)
        assert result == "async_value"
    
    def test_make_key(self):
        """Тест создания ключей"""
        cache = CacheManager()
        
        # Обычный ключ
        key = cache.make_key("user", "123", "profile")
        assert key == "user:123:profile"
        
        # Длинный ключ должен быть захеширован
        long_parts = ["part"] * 50
        long_key = cache.make_key(*long_parts)
        assert len(long_key) == 32  # MD5 hash
    
    def test_stats(self):
        """Тест статистики кеша"""
        cache = CacheManager()
        
        # Начальная статистика
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0
        
        # Сброс статистики
        cache.reset_stats()
        stats = cache.get_stats()
        assert all(v == 0 for v in stats.values() if v != stats["hit_rate"])


class TestCacheMiddleware:
    """Тесты middleware кеширования"""
    
    @pytest.mark.asyncio
    async def test_cache_middleware_get_request(self):
        """Тест кеширования GET запроса"""
        cache_manager = CacheManager()
        middleware = CacheMiddleware(cache_manager, default_expire=60)
        
        # Создаем мок запроса
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "query_string": b"",
            "headers": []
        }
        request = Request(scope, None)
        
        # Мок функции call_next
        response_data = {"data": "test_response"}
        mock_response = JSONResponse(response_data)
        
        async def call_next(req):
            return mock_response
        
        # Первый вызов - должен кешировать
        response1 = await middleware(request, call_next)
        assert response1.get_header("X-Cache") == "MISS"
        
        # Второй вызов - должен вернуть из кеша
        response2 = await middleware(request, call_next)
        assert response2.get_header("X-Cache") == "HIT"
    
    @pytest.mark.asyncio
    async def test_cache_middleware_post_request(self):
        """Тест что POST запросы не кешируются"""
        cache_manager = CacheManager()
        middleware = CacheMiddleware(cache_manager)
        
        # Создаем POST запрос
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/test",
            "query_string": b"",
            "headers": []
        }
        request = Request(scope, None)
        
        mock_response = JSONResponse({"data": "test"})
        
        async def call_next(req):
            return mock_response
        
        response = await middleware(request, call_next)
        assert response.get_header("X-Cache") == "SKIP"
    
    @pytest.mark.asyncio
    async def test_cache_middleware_skip_paths(self):
        """Тест пропуска определенных путей"""
        cache_manager = CacheManager()
        middleware = CacheMiddleware(
            cache_manager,
            skip_paths={"/api/admin", "/api/private"}
        )
        
        # Создаем запрос к пропускаемому пути
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/admin",
            "query_string": b"",
            "headers": []
        }
        request = Request(scope, None)
        
        mock_response = JSONResponse({"data": "admin"})
        
        async def call_next(req):
            return mock_response
        
        response = await middleware(request, call_next)
        assert response.get_header("X-Cache") == "SKIP"
    
    @pytest.mark.asyncio
    async def test_cache_middleware_error_response(self):
        """Тест что ошибки не кешируются"""
        cache_manager = CacheManager()
        middleware = CacheMiddleware(cache_manager)
        
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/error",
            "query_string": b"",
            "headers": []
        }
        request = Request(scope, None)
        
        # Возвращаем ошибку
        error_response = JSONResponse({"error": "Not found"}, status_code=404)
        
        async def call_next(req):
            return error_response
        
        response = await middleware(request, call_next)
        assert response.get_header("X-Cache") == "SKIP"
        assert response.status_code == 404


class TestCacheEntry:
    """Тесты записи кеша"""
    
    def test_cache_entry_creation(self):
        """Тест создания записи кеша"""
        entry = CacheEntry("test_value")
        assert entry.value == "test_value"
        assert entry.expires_at is None
        assert entry.created_at is not None
        assert not entry.is_expired()
    
    def test_cache_entry_with_expiration(self):
        """Тест записи с истечением"""
        expires_at = time.time() + 1
        entry = CacheEntry("test_value", expires_at=expires_at)
        
        assert not entry.is_expired()
        
        # Симулируем истечение времени
        entry.expires_at = time.time() - 1
        assert entry.is_expired()


if __name__ == "__main__":
    pytest.main([__file__])


