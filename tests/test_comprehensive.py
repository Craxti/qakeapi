"""
Комплексные тесты QakeAPI для расширенного покрытия
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from qakeapi import HTTPException, JSONResponse, QakeAPI, Request
from qakeapi.core.router import APIRouter
from qakeapi.middleware.cors import CORSMiddleware
from qakeapi.middleware.logging import LoggingMiddleware
from qakeapi.utils.validation import (
    DataValidator,
    DictValidator,
    IntegerValidator,
    StringValidator,
)


class TestComprehensiveAPI:
    """Комплексные тесты API"""

    @pytest.fixture
    def app(self):
        """Создать тестовое приложение"""
        app = QakeAPI(
            title="Test API",
            description="Test Description",
            version="1.0.0",
            debug=True,
        )

        # Добавляем middleware
        app.add_middleware(
            CORSMiddleware(
                allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
            )
        )

        # Базовые маршруты
        @app.get("/")
        async def root():
            return {"message": "Hello World"}

        @app.get("/items/{item_id}")
        async def get_item(item_id: str, q: str = None):
            return {"item_id": item_id, "q": q}

        @app.post("/items")
        async def create_item(request: Request):
            data = await request.json()
            return {"created": data}

        @app.put("/items/{item_id}")
        async def update_item(item_id: str, request: Request):
            data = await request.json()
            return {"item_id": item_id, "updated": data}

        @app.delete("/items/{item_id}")
        async def delete_item(item_id: str):
            return {"deleted": item_id}

        # Маршрут с исключением
        @app.get("/error")
        async def error_endpoint():
            raise HTTPException(status_code=400, detail="Test error")

        # Маршрут с валидацией
        validator = DataValidator(
            {
                "name": StringValidator(min_length=1, max_length=100),
                "age": IntegerValidator(min_value=0, max_value=150),
            }
        )

        @app.post("/validate")
        async def validate_data(request: Request):
            data = await request.json()
            result = validator.validate(data)
            if not result.is_valid:
                raise HTTPException(status_code=422, detail=result.errors)
            return {"validated": result.data}

        return app

    @pytest.mark.asyncio
    async def test_root_endpoint(self, app):
        """Тест корневого эндпоинта"""
        # Создаем mock запрос
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [],
        }

        receive = AsyncMock()
        send = AsyncMock()

        await app(scope, receive, send)

        # Проверяем, что send был вызван с правильными данными
        assert send.call_count >= 2  # response.start + response.body

    @pytest.mark.asyncio
    async def test_path_parameters(self, app):
        """Тест параметров пути"""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/items/123",
            "query_string": b"q=test",
            "headers": [],
        }

        receive = AsyncMock()
        send = AsyncMock()

        await app(scope, receive, send)
        assert send.call_count >= 2

    @pytest.mark.asyncio
    async def test_post_request(self, app):
        """Тест POST запроса"""
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/items",
            "query_string": b"",
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", b"15"),
            ],
        }

        receive = AsyncMock()
        receive.side_effect = [
            {"type": "http.request", "body": b'{"test": "data"}', "more_body": False}
        ]

        send = AsyncMock()

        await app(scope, receive, send)
        assert send.call_count >= 2

    @pytest.mark.asyncio
    async def test_error_handling(self, app):
        """Тест обработки ошибок"""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/error",
            "query_string": b"",
            "headers": [],
        }

        receive = AsyncMock()
        send = AsyncMock()

        await app(scope, receive, send)

        # Проверяем, что ошибка была обработана
        assert send.call_count >= 2

        # Проверяем статус код ошибки
        start_call = send.call_args_list[0][0][0]
        assert start_call["status"] == 400

    @pytest.mark.asyncio
    async def test_validation_success(self, app):
        """Тест успешной валидации"""
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/validate",
            "query_string": b"",
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", b"25"),
            ],
        }

        receive = AsyncMock()
        receive.side_effect = [
            {
                "type": "http.request",
                "body": b'{"name": "John", "age": 30}',
                "more_body": False,
            }
        ]

        send = AsyncMock()

        await app(scope, receive, send)

        # Проверяем успешный ответ
        start_call = send.call_args_list[0][0][0]
        assert start_call["status"] == 200

    @pytest.mark.asyncio
    async def test_validation_error(self, app):
        """Тест ошибки валидации"""
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/validate",
            "query_string": b"",
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", b"20"),
            ],
        }

        receive = AsyncMock()
        receive.side_effect = [
            {
                "type": "http.request",
                "body": b'{"name": "", "age": -1}',
                "more_body": False,
            }
        ]

        send = AsyncMock()

        await app(scope, receive, send)

        # Проверяем ошибку валидации
        start_call = send.call_args_list[0][0][0]
        assert start_call["status"] == 422

    def test_openapi_generation(self, app):
        """Тест генерации OpenAPI схемы"""
        schema = app.openapi()

        assert schema["openapi"] == "3.0.2"
        assert schema["info"]["title"] == "Test API"
        assert schema["info"]["version"] == "1.0.0"
        assert "paths" in schema
        assert "/" in schema["paths"]
        assert "/items/{item_id}" in schema["paths"]

    def test_middleware_registration(self, app):
        """Тест регистрации middleware"""
        assert len(app.middleware_stack.middleware) > 0

        # Проверяем, что CORS middleware зарегистрирован
        cors_found = any(
            isinstance(mw, CORSMiddleware) for mw in app.middleware_stack.middleware
        )
        assert cors_found

    def test_exception_handler_registration(self, app):
        """Тест регистрации обработчиков исключений"""
        assert HTTPException in app.exception_handlers
        assert Exception in app.exception_handlers

    @pytest.mark.asyncio
    async def test_lifespan_events(self, app):
        """Тест событий жизненного цикла"""
        startup_called = False
        shutdown_called = False

        @app.on_event("startup")
        async def startup():
            nonlocal startup_called
            startup_called = True

        @app.on_event("shutdown")
        async def shutdown():
            nonlocal shutdown_called
            shutdown_called = True

        # Тест startup и shutdown
        scope = {"type": "lifespan"}

        # Создаем правильную последовательность lifespan событий
        messages = [{"type": "lifespan.startup"}, {"type": "lifespan.shutdown"}]
        message_iter = iter(messages)

        async def receive():
            try:
                return next(message_iter)
            except StopIteration:
                # Возвращаем disconnect для завершения
                return {"type": "lifespan.disconnect"}

        send = AsyncMock()

        await app(scope, receive, send)

        assert startup_called
        assert shutdown_called


class TestAPIRouter:
    """Тесты APIRouter"""

    def test_router_creation(self):
        """Тест создания роутера"""
        router = APIRouter(prefix="/api", tags=["test"])

        assert router.prefix == "/api"
        assert router.tags == ["test"]
        assert len(router.routes) == 0

    def test_route_registration(self):
        """Тест регистрации маршрутов"""
        router = APIRouter()

        @router.get("/test")
        async def test_route():
            return {"test": True}

        assert len(router.routes) == 1
        assert router.routes[0].path == "/test"
        assert "GET" in router.routes[0].methods

    def test_router_inclusion(self):
        """Тест включения роутера в приложение"""
        app = QakeAPI()
        router = APIRouter(prefix="/api")

        @router.get("/test")
        async def test_route():
            return {"test": True}

        app.include_router(router)

        # Проверяем, что маршрут добавлен с префиксом
        api_routes = [r for r in app.routes if r.path.startswith("/api")]
        assert len(api_routes) == 1
        assert api_routes[0].path == "/api/test"


class TestMiddleware:
    """Тесты middleware"""

    @pytest.mark.asyncio
    async def test_cors_middleware(self):
        """Тест CORS middleware"""
        cors = CORSMiddleware(
            allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"]
        )

        # Создаем mock запрос
        request = Mock()
        request.method = "GET"
        request.get_header = Mock(return_value="http://localhost")

        # Создаем mock call_next
        call_next = AsyncMock()
        response = Mock()
        response.headers = {}
        call_next.return_value = response

        result = await cors(request, call_next)

        assert call_next.called
        assert "Access-Control-Allow-Origin" in result.headers

    @pytest.mark.asyncio
    async def test_logging_middleware(self):
        """Тест logging middleware"""
        logger = Mock()
        logging_mw = LoggingMiddleware(logger=logger)

        # Создаем mock запрос
        request = Mock()
        request.method = "GET"
        request.path = "/test"
        request.query_string = ""
        request.headers = {}
        request.client = ("127.0.0.1", 12345)
        request.get_header = Mock(return_value="test-agent")
        request.body = AsyncMock(return_value=b"")

        # Создаем mock call_next
        call_next = AsyncMock()
        response = Mock()
        response.status_code = 200
        response.headers = {}
        call_next.return_value = response

        result = await logging_mw(request, call_next)

        assert call_next.called
        assert logger.info.called


class TestValidation:
    """Дополнительные тесты валидации"""

    def test_complex_validation(self):
        """Тест сложной валидации"""
        validator = DataValidator(
            {
                "user": DictValidator(
                    {
                        "name": StringValidator(min_length=2),
                        "email": StringValidator(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$"),
                        "age": IntegerValidator(min_value=0, max_value=120),
                    }
                ),
                "preferences": DictValidator(
                    {
                        "theme": StringValidator(required=False),
                        "notifications": StringValidator(required=False),
                    }
                ),
            }
        )

        # Валидные данные
        valid_data = {
            "user": {"name": "John Doe", "email": "john@example.com", "age": 30},
            "preferences": {"theme": "dark"},
        }

        result = validator.validate(valid_data)
        assert result.is_valid
        assert result.data["user"]["name"] == "John Doe"

    def test_validation_errors(self):
        """Тест ошибок валидации"""
        validator = DataValidator(
            {
                "name": StringValidator(min_length=5),
                "age": IntegerValidator(min_value=18),
            }
        )

        invalid_data = {"name": "Jo", "age": 15}  # Слишком короткое  # Слишком молодой

        result = validator.validate(invalid_data)
        assert not result.is_valid
        assert any("name" in error for error in result.errors)
        assert any("age" in error for error in result.errors)


class TestUtilities:
    """Тесты утилит"""

    def test_status_codes(self):
        """Тест HTTP статус кодов"""
        from qakeapi.utils.status import status

        assert status.OK == 200
        assert status.CREATED == 201
        assert status.BAD_REQUEST == 400
        assert status.NOT_FOUND == 404
        assert status.INTERNAL_SERVER_ERROR == 500

    def test_json_response(self):
        """Тест JSON ответа"""
        data = {"message": "test", "status": "ok"}
        response = JSONResponse(content=data, status_code=201)

        assert response.status_code == 201
        assert response.media_type == "application/json"

    def test_http_exception(self):
        """Тест HTTP исключения"""
        exc = HTTPException(status_code=404, detail="Not found")

        assert exc.status_code == 404
        assert exc.detail == "Not found"
        assert exc.headers == {}

        # С заголовками
        exc_with_headers = HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

        assert exc_with_headers.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_async_context_manager():
    """Тест асинхронного контекстного менеджера"""
    app = QakeAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"test": True}

    # Проверяем, что приложение можно использовать как async context manager
    # (это базовая проверка структуры)
    assert hasattr(app, "__call__")
    assert asyncio.iscoroutinefunction(app.__call__)


def test_app_metadata():
    """Тест метаданных приложения"""
    app = QakeAPI(title="Test App", description="Test Description", version="2.0.0")

    assert app.title == "Test App"
    assert app.description == "Test Description"
    assert app.version == "2.0.0"


def test_debug_mode():
    """Тест debug режима"""
    app_debug = QakeAPI(debug=True)
    app_prod = QakeAPI(debug=False)

    assert app_debug.debug is True
    assert app_prod.debug is False
