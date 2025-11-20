"""
Тесты middleware компрессии
"""

import pytest
import gzip
import zlib
from unittest.mock import Mock

from qakeapi.middleware.compression import CompressionMiddleware
from qakeapi.core.request import Request
from qakeapi.core.responses import Response, JSONResponse


class TestCompressionMiddleware:
    """Тесты middleware компрессии"""

    @pytest.mark.asyncio
    async def test_gzip_compression(self):
        """Тест gzip компрессии"""
        middleware = CompressionMiddleware(minimum_size=10)

        # Создаем запрос с поддержкой gzip
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [(b"accept-encoding", b"gzip, deflate")],
        }
        request = Request(scope, None)

        # Создаем большой ответ
        large_content = "This is a large response that should be compressed " * 20
        original_response = Response(large_content, media_type="text/plain")

        async def call_next(req):
            return original_response

        # Применяем middleware
        response = await middleware(request, call_next)

        # Проверяем, что ответ сжат
        assert response.get_header("Content-Encoding") == "gzip"
        assert response.get_header("Vary") == "Accept-Encoding"
        assert len(response.body) < len(large_content.encode())

        # Проверяем, что можем распаковать
        decompressed = gzip.decompress(response.body).decode()
        assert decompressed == large_content

    @pytest.mark.asyncio
    async def test_no_compression_small_response(self):
        """Тест что маленькие ответы не сжимаются"""
        middleware = CompressionMiddleware(minimum_size=100)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [(b"accept-encoding", b"gzip")],
        }
        request = Request(scope, None)

        small_content = "Small"
        original_response = Response(small_content, media_type="text/plain")

        async def call_next(req):
            return original_response

        response = await middleware(request, call_next)

        # Проверяем, что сжатие не применилось
        assert response.get_header("Content-Encoding") is None
        assert response.body == small_content.encode()

    @pytest.mark.asyncio
    async def test_no_compression_unsupported_client(self):
        """Тест что не сжимаем для клиентов без поддержки"""
        middleware = CompressionMiddleware(minimum_size=10)

        # Запрос без поддержки сжатия
        scope = {"type": "http", "method": "GET", "path": "/api/test", "headers": []}
        request = Request(scope, None)

        large_content = "This is a large response " * 20
        original_response = Response(large_content, media_type="text/plain")

        async def call_next(req):
            return original_response

        response = await middleware(request, call_next)

        # Проверяем, что сжатие не применилось
        assert response.get_header("Content-Encoding") is None
        assert response.body == large_content.encode()

    @pytest.mark.asyncio
    async def test_no_compression_incompressible_type(self):
        """Тест что не сжимаем несжимаемые типы"""
        middleware = CompressionMiddleware(minimum_size=10)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [(b"accept-encoding", b"gzip")],
        }
        request = Request(scope, None)

        # Бинарный контент (например, изображение)
        binary_content = b"Binary data " * 50
        original_response = Response(binary_content, media_type="image/jpeg")

        async def call_next(req):
            return original_response

        response = await middleware(request, call_next)

        # Проверяем, что сжатие не применилось
        assert response.get_header("Content-Encoding") is None
        assert response.body == binary_content

    @pytest.mark.asyncio
    async def test_json_compression(self):
        """Тест сжатия JSON ответов"""
        middleware = CompressionMiddleware(minimum_size=10)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [(b"accept-encoding", b"gzip")],
        }
        request = Request(scope, None)

        # Большой JSON ответ
        large_data = {"items": [{"id": i, "name": f"Item {i}"} for i in range(100)]}
        original_response = JSONResponse(large_data)

        async def call_next(req):
            return original_response

        response = await middleware(request, call_next)

        # Проверяем, что ответ сжат
        assert response.get_header("Content-Encoding") == "gzip"
        assert response.get_header("Vary") == "Accept-Encoding"

        # Проверяем, что можем распаковать JSON
        decompressed = gzip.decompress(response.body)
        import json

        data = json.loads(decompressed.decode())
        assert len(data["items"]) == 100

    @pytest.mark.asyncio
    async def test_deflate_compression(self):
        """Тест deflate компрессии"""
        middleware = CompressionMiddleware(minimum_size=10)

        # Запрос с поддержкой только deflate
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [(b"accept-encoding", b"deflate")],
        }
        request = Request(scope, None)

        large_content = "This is a large response for deflate " * 20
        original_response = Response(large_content, media_type="text/plain")

        async def call_next(req):
            return original_response

        response = await middleware(request, call_next)

        # Проверяем, что ответ сжат deflate
        assert response.get_header("Content-Encoding") == "deflate"
        assert len(response.body) < len(large_content.encode())

        # Проверяем, что можем распаковать
        decompressed = zlib.decompress(response.body).decode()
        assert decompressed == large_content

    @pytest.mark.asyncio
    async def test_skip_paths(self):
        """Тест пропуска определенных путей"""
        middleware = CompressionMiddleware(
            minimum_size=10, skip_paths={"/api/raw", "/api/binary"}
        )

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/raw",
            "headers": [(b"accept-encoding", b"gzip")],
        }
        request = Request(scope, None)

        large_content = "This should not be compressed " * 20
        original_response = Response(large_content, media_type="text/plain")

        async def call_next(req):
            return original_response

        response = await middleware(request, call_next)

        # Проверяем, что сжатие не применилось
        assert response.get_header("Content-Encoding") is None
        assert response.body == large_content.encode()

    @pytest.mark.asyncio
    async def test_already_compressed_response(self):
        """Тест что уже сжатые ответы не сжимаются повторно"""
        middleware = CompressionMiddleware(minimum_size=10)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [(b"accept-encoding", b"gzip")],
        }
        request = Request(scope, None)

        large_content = "Already compressed content " * 20
        original_response = Response(large_content, media_type="text/plain")
        original_response.set_header("Content-Encoding", "br")  # Уже сжато brotli

        async def call_next(req):
            return original_response

        response = await middleware(request, call_next)

        # Проверяем, что повторное сжатие не применилось
        assert response.get_header("Content-Encoding") == "br"
        assert response.body == large_content.encode()

    @pytest.mark.asyncio
    async def test_compression_level(self):
        """Тест уровня сжатия"""
        # Высокий уровень сжатия
        high_compression = CompressionMiddleware(minimum_size=10, compression_level=9)

        # Низкий уровень сжатия
        low_compression = CompressionMiddleware(minimum_size=10, compression_level=1)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [(b"accept-encoding", b"gzip")],
        }
        request = Request(scope, None)

        # Контент с хорошей сжимаемостью
        repetitive_content = "AAAAAAAAAA" * 100

        async def call_next(req):
            return Response(repetitive_content, media_type="text/plain")

        # Тестируем высокое сжатие
        high_response = await high_compression(request, call_next)
        high_size = len(high_response.body)

        # Тестируем низкое сжатие
        low_response = await low_compression(request, call_next)
        low_size = len(low_response.body)

        # Высокое сжатие должно давать меньший размер
        assert high_size <= low_size

        # Оба должны быть сжаты
        assert high_response.get_header("Content-Encoding") == "gzip"
        assert low_response.get_header("Content-Encoding") == "gzip"

    def test_should_compress_logic(self):
        """Тест логики определения необходимости сжатия"""
        middleware = CompressionMiddleware(
            minimum_size=100, compressible_types={"text/plain", "application/json"}
        )

        # Создаем мок запроса с поддержкой gzip
        scope = {"type": "http", "headers": [(b"accept-encoding", b"gzip, deflate")]}
        request = Request(scope, None)

        # Маленький ответ - не должен сжиматься
        small_response = Response("small", media_type="text/plain")
        assert not middleware._should_compress(request, small_response)

        # Большой ответ с поддерживаемым типом - должен сжиматься
        large_response = Response("a" * 200, media_type="text/plain")
        assert middleware._should_compress(request, large_response)

        # Большой ответ с неподдерживаемым типом - не должен сжиматься
        binary_response = Response(b"a" * 200, media_type="image/jpeg")
        assert not middleware._should_compress(request, binary_response)


if __name__ == "__main__":
    pytest.main([__file__])
