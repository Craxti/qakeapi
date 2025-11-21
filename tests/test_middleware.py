"""
Тесты для middleware
"""

import pytest
from qakeapi import QakeAPI
from qakeapi.middleware.cors import CORSMiddleware
from qakeapi.middleware.logging import LoggingMiddleware
from qakeapi.middleware.auth import (
    BearerTokenMiddleware,
    BasicAuthMiddleware,
    APIKeyMiddleware,
)


@pytest.fixture
def app():
    """Создать тестовое приложение"""
    app = QakeAPI(title="Test App", debug=True)

    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    @app.get("/protected")
    async def protected():
        return {"message": "Protected endpoint"}

    return app


@pytest.fixture
def client(app):
    """Создать тестовый клиент"""
    from httpx import AsyncClient

    return AsyncClient(app=app, base_url="http://testserver")


class TestCORSMiddleware:
    """Тесты CORS middleware"""

    @pytest.mark.asyncio
    async def test_cors_simple_request(self):
        """Тест простого CORS запроса"""
        app = QakeAPI()
        app.add_middleware(CORSMiddleware(allow_origins=["*"]))

        @app.get("/")
        async def root():
            return {"message": "Hello"}

        from httpx import AsyncClient

        from httpx import AsyncClient

        try:
            from httpx import ASGITransport
        except ImportError:
            from httpx._transports.asgi import ASGITransport

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.get("/", headers={"Origin": "http://example.com"})

            assert response.status_code == 200
            assert (
                response.headers.get("access-control-allow-origin")
                == "http://example.com"
            )

    @pytest.mark.asyncio
    async def test_cors_preflight_request(self):
        """Тест preflight CORS запроса"""
        app = QakeAPI()
        app.add_middleware(
            CORSMiddleware(
                allow_origins=["http://example.com"],
                allow_methods=["GET", "POST"],
                allow_headers=["Content-Type"],
            )
        )

        @app.post("/")
        async def root():
            return {"message": "Hello"}

        from httpx import AsyncClient

        from httpx import AsyncClient

        try:
            from httpx import ASGITransport
        except ImportError:
            from httpx._transports.asgi import ASGITransport

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.options(
                "/",
                headers={
                    "Origin": "http://example.com",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type",
                },
            )

            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers
            assert "access-control-allow-methods" in response.headers

    @pytest.mark.asyncio
    async def test_cors_credentials(self):
        """Тест CORS с credentials"""
        app = QakeAPI()
        app.add_middleware(
            CORSMiddleware(allow_origins=["http://example.com"], allow_credentials=True)
        )

        @app.get("/")
        async def root():
            return {"message": "Hello"}

        from httpx import AsyncClient

        from httpx import AsyncClient

        try:
            from httpx import ASGITransport
        except ImportError:
            from httpx._transports.asgi import ASGITransport

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.get("/", headers={"Origin": "http://example.com"})

            assert response.status_code == 200
            assert response.headers.get("access-control-allow-credentials") == "true"


class TestAuthMiddleware:
    """Тесты authentication middleware"""

    @pytest.mark.asyncio
    async def test_bearer_token_middleware(self):
        """Тест Bearer token middleware"""
        app = QakeAPI()
        app.add_middleware(
            BearerTokenMiddleware(secret_key="test-secret", skip_paths={"/", "/public"})
        )

        @app.get("/")
        async def public():
            return {"message": "Public"}

        @app.get("/protected")
        async def protected():
            return {"message": "Protected"}

        from httpx import AsyncClient

        from httpx import AsyncClient

        try:
            from httpx import ASGITransport
        except ImportError:
            from httpx._transports.asgi import ASGITransport

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            # Публичный endpoint должен работать без токена
            response = await client.get("/")
            assert response.status_code == 200

            # Защищенный endpoint должен требовать токен
            response = await client.get("/protected")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_basic_auth_middleware(self):
        """Тест Basic auth middleware"""
        app = QakeAPI()
        app.add_middleware(
            BasicAuthMiddleware(
                users={"admin": "password", "user": "secret"}, skip_paths={"/"}
            )
        )

        @app.get("/")
        async def public():
            return {"message": "Public"}

        @app.get("/protected")
        async def protected():
            return {"message": "Protected"}

        from httpx import AsyncClient
        import base64

        from httpx import AsyncClient

        try:
            from httpx import ASGITransport
        except ImportError:
            from httpx._transports.asgi import ASGITransport

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            # Публичный endpoint
            response = await client.get("/")
            assert response.status_code == 200

            # Защищенный endpoint без авторизации
            response = await client.get("/protected")
            assert response.status_code == 401
            assert "www-authenticate" in response.headers

            # Защищенный endpoint с правильными credentials
            credentials = base64.b64encode(b"admin:password").decode()
            response = await client.get(
                "/protected", headers={"Authorization": f"Basic {credentials}"}
            )
            assert response.status_code == 200

            # Защищенный endpoint с неправильными credentials
            credentials = base64.b64encode(b"admin:wrong").decode()
            response = await client.get(
                "/protected", headers={"Authorization": f"Basic {credentials}"}
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_api_key_middleware(self):
        """Тест API key middleware"""
        app = QakeAPI()
        app.add_middleware(
            APIKeyMiddleware(
                api_keys={"test-key": {"name": "Test Client"}},
                header_name="X-API-Key",
                skip_paths={"/"},
            )
        )

        @app.get("/")
        async def public():
            return {"message": "Public"}

        @app.get("/protected")
        async def protected():
            return {"message": "Protected"}

        from httpx import AsyncClient

        from httpx import AsyncClient

        try:
            from httpx import ASGITransport
        except ImportError:
            from httpx._transports.asgi import ASGITransport

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            # Публичный endpoint
            response = await client.get("/")
            assert response.status_code == 200

            # Защищенный endpoint без API ключа
            response = await client.get("/protected")
            assert response.status_code == 401

            # Защищенный endpoint с правильным API ключом
            response = await client.get("/protected", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200

            # Защищенный endpoint с неправильным API ключом
            response = await client.get(
                "/protected", headers={"X-API-Key": "wrong-key"}
            )
            assert response.status_code == 401


class TestLoggingMiddleware:
    """Тесты logging middleware"""

    @pytest.mark.asyncio
    async def test_logging_middleware(self):
        """Тест logging middleware"""
        import logging
        from io import StringIO

        # Создаем тестовый логгер
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger("test_logger")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        app = QakeAPI()
        app.add_middleware(LoggingMiddleware(logger=logger))

        @app.get("/")
        async def root():
            return {"message": "Hello"}

        from httpx import AsyncClient

        from httpx import AsyncClient

        try:
            from httpx import ASGITransport
        except ImportError:
            from httpx._transports.asgi import ASGITransport

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.get("/")
            assert response.status_code == 200

        # Проверяем, что запрос был залогирован
        log_output = log_stream.getvalue()
        assert "Request started" in log_output
        assert "Request completed" in log_output
        assert "GET /" in log_output


if __name__ == "__main__":
    pytest.main([__file__])
