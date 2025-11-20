"""
Базовые тесты для QakeAPI
"""
import pytest
import asyncio
from qakeapi import QakeAPI, Request, JSONResponse
from qakeapi.core.exceptions import HTTPException
from qakeapi.utils.status import status


@pytest.fixture
def app():
    """Создать тестовое приложение"""
    app = QakeAPI(title="Test App", debug=True)

    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    @app.get("/items/{item_id}")
    async def get_item(item_id: str, q: str = None):  # Изменили на str
        return {"item_id": item_id, "q": q}

    @app.post("/items/")
    async def create_item(request: Request):
        data = await request.json()
        return {"message": "Created", "data": data}

    @app.get("/error")
    async def error_endpoint():
        raise HTTPException(status.BAD_REQUEST, "Test error")

    return app


@pytest.fixture
def client(app):
    """Создать тестовый клиент"""
    from httpx import AsyncClient

    return AsyncClient(app=app, base_url="http://testserver")


class TestBasicRoutes:
    """Тесты базовых маршрутов"""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Тест главной страницы"""
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}

    @pytest.mark.asyncio
    async def test_path_parameters(self, client):
        """Тест параметров пути"""
        response = await client.get("/items/42")
        assert response.status_code == 200
        data = response.json()
        assert data["item_id"] == "42"  # Параметры пути возвращаются как строки
        assert data["q"] is None

    @pytest.mark.asyncio
    async def test_query_parameters(self, client):
        """Тест query параметров"""
        response = await client.get("/items/42?q=test")
        assert response.status_code == 200
        data = response.json()
        assert data["item_id"] == "42"  # Параметры пути возвращаются как строки
        assert data["q"] == "test"

    @pytest.mark.asyncio
    async def test_post_request(self, client):
        """Тест POST запроса"""
        test_data = {"name": "Test Item", "price": 10.5}
        response = await client.post("/items/", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Created"
        assert data["data"] == test_data

    @pytest.mark.asyncio
    async def test_http_exception(self, client):
        """Тест HTTP исключений"""
        response = await client.get("/error")
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Test error"

    @pytest.mark.asyncio
    async def test_not_found(self, client):
        """Тест 404 ошибки"""
        response = await client.get("/nonexistent")
        assert response.status_code == 404


class TestApplication:
    """Тесты класса приложения"""

    def test_app_creation(self):
        """Тест создания приложения"""
        app = QakeAPI(
            title="Test App",
            description="Test Description",
            version="1.0.0",
            debug=True,
        )

        assert app.title == "Test App"
        assert app.description == "Test Description"
        assert app.version == "1.0.0"
        assert app.debug is True

    def test_route_registration(self):
        """Тест регистрации маршрутов"""
        app = QakeAPI()

        @app.get("/test")
        async def test_route():
            return {"test": True}

        # Проверяем, что маршрут зарегистрирован
        assert len(app.routes) > 0
        route_paths = [route.path for route in app.routes]
        assert "/test" in route_paths

    def test_middleware_registration(self):
        """Тест регистрации middleware"""
        from qakeapi.middleware.cors import CORSMiddleware

        app = QakeAPI()
        cors_middleware = CORSMiddleware()
        app.add_middleware(cors_middleware)

        assert cors_middleware in app.middleware_stack

    def test_exception_handler_registration(self):
        """Тест регистрации обработчиков исключений"""
        app = QakeAPI()

        @app.exception_handler(ValueError)
        async def value_error_handler(request, exc):
            return JSONResponse({"error": "Value error"}, status_code=400)

        assert ValueError in app.exception_handlers


class TestRouter:
    """Тесты роутера"""

    def test_path_matching(self):
        """Тест сопоставления путей"""
        from qakeapi.core.router import Route, RouteType

        # Простой путь
        route = Route("/users", lambda: None, ["GET"])
        assert route.matches("/users", "GET") == {}
        assert route.matches("/users", "POST") is None
        assert route.matches("/items", "GET") is None

        # Путь с параметром
        route = Route("/users/{user_id}", lambda: None, ["GET"])
        params = route.matches("/users/123", "GET")
        assert params == {"user_id": "123"}

        # Типизированный параметр
        route = Route("/users/{user_id:int}", lambda: None, ["GET"])
        params = route.matches("/users/123", "GET")
        assert params == {"user_id": "123"}

        # Path параметр
        route = Route("/files/{file_path:path}", lambda: None, ["GET"])
        params = route.matches("/files/docs/readme.txt", "GET")
        assert params == {"file_path": "docs/readme.txt"}


if __name__ == "__main__":
    pytest.main([__file__])
