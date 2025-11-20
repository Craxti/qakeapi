"""
Тесты новых возможностей QakeAPI
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from qakeapi import QakeAPI
from qakeapi.core.application import QakeAPI as QakeAPICore


class TestNewFeatures:
    """Тесты новых возможностей"""

    def test_import_availability(self):
        """Тест доступности импортов"""
        # Проверяем, что основные компоненты импортируются
        from qakeapi import (
            QakeAPI,
            Request,
            JSONResponse,
            HTTPException,
            CORSMiddleware,
            LoggingMiddleware,
        )

        assert QakeAPI is not None
        assert Request is not None
        assert JSONResponse is not None
        assert HTTPException is not None
        assert CORSMiddleware is not None
        assert LoggingMiddleware is not None

    def test_optional_imports(self):
        """Тест опциональных импортов"""
        # Проверяем, что опциональные модули импортируются (как заглушки если недоступны)
        from qakeapi import MetricsCollector, HealthChecker, JWTManager, CacheManager

        # Должны быть доступны (как заглушки или реальные классы)
        assert MetricsCollector is not None
        assert HealthChecker is not None
        assert JWTManager is not None
        assert CacheManager is not None

    def test_template_renderer_import(self):
        """Тест импорта TemplateRenderer"""
        from qakeapi import TemplateRenderer

        assert TemplateRenderer is not None

    def test_error_handling_import(self):
        """Тест импорта обработки ошибок"""
        from qakeapi import ErrorHandler, create_error_handler

        assert ErrorHandler is not None
        assert create_error_handler is not None

    def test_application_creation_with_new_features(self):
        """Тест создания приложения с новыми возможностями"""
        app = QakeAPI(
            title="Enhanced App",
            description="App with new features",
            version="1.0.0",
            debug=True,
        )

        assert app.title == "Enhanced App"
        assert app.debug is True

        # Проверяем, что middleware stack существует
        assert hasattr(app, "middleware_stack")
        assert isinstance(app.middleware_stack, list)

    def test_middleware_chain_fix(self):
        """Тест исправления цепочки middleware"""
        app = QakeAPI()

        # Добавляем несколько middleware
        from qakeapi.middleware.cors import CORSMiddleware
        from qakeapi.middleware.logging import LoggingMiddleware

        app.add_middleware(CORSMiddleware())
        app.add_middleware(LoggingMiddleware())

        assert len(app.middleware_stack) == 2

        # Проверяем, что метод _apply_middleware существует и не вызывает рекурсию
        assert hasattr(app, "_apply_middleware")

    @pytest.mark.asyncio
    async def test_middleware_execution(self):
        """Тест выполнения middleware без рекурсии"""
        app = QakeAPI()

        # Создаем простой middleware
        class TestMiddleware:
            def __init__(self):
                self.called = False

            def create_wrapper(self, call_next):
                async def wrapper(request):
                    self.called = True
                    return await call_next(request)

                return wrapper

        test_mw = TestMiddleware()
        app.middleware_stack.append(test_mw)

        # Создаем mock запрос и call_next
        request = Mock()
        call_next = AsyncMock()
        call_next.return_value = Mock()

        # Выполняем middleware
        await app._apply_middleware(request, call_next)

        assert test_mw.called
        assert call_next.called

    def test_openapi_enhancement(self):
        """Тест улучшенной OpenAPI схемы"""
        app = QakeAPI(
            title="API with OpenAPI",
            description="Enhanced OpenAPI schema",
            version="2.0.0",
        )

        @app.get("/test")
        async def test_endpoint():
            return {"test": True}

        schema = app.openapi()

        assert schema["openapi"] == "3.0.2"
        assert schema["info"]["title"] == "API with OpenAPI"
        assert schema["info"]["description"] == "Enhanced OpenAPI schema"
        assert schema["info"]["version"] == "2.0.0"
        assert "/test" in schema["paths"]

    def test_exception_handlers_enhancement(self):
        """Тест улучшенных обработчиков исключений"""
        app = QakeAPI()

        # Проверяем базовые обработчики
        from qakeapi.core.exceptions import HTTPException, QakeAPIException

        assert HTTPException in app.exception_handlers
        assert QakeAPIException in app.exception_handlers
        assert Exception in app.exception_handlers

        # Добавляем кастомный обработчик
        @app.exception_handler(ValueError)
        async def value_error_handler(request, exc):
            return {"error": "Value error", "detail": str(exc)}

        assert ValueError in app.exception_handlers

    @pytest.mark.asyncio
    async def test_lifespan_events(self):
        """Тест событий жизненного цикла"""
        app = QakeAPI()

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

        # Проверяем, что обработчики добавлены
        assert len(app.on_startup_handlers) == 1
        assert len(app.on_shutdown_handlers) == 1

        # Выполняем startup
        await app._startup()
        assert startup_called

        # Выполняем shutdown
        await app._shutdown()
        assert shutdown_called

    def test_static_files_integration(self):
        """Тест интеграции статических файлов"""
        from qakeapi.utils.static import StaticFiles

        app = QakeAPI()

        # Проверяем, что можно монтировать статические файлы
        # (создаем временную директорию для теста)
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем тестовый файл
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test content")

            static_files = StaticFiles(directory=temp_dir)
            assert static_files.directory.exists()

    def test_template_integration(self):
        """Тест интеграции шаблонов"""
        from qakeapi.utils.templates import TemplateRenderer, SimpleTemplates

        # Проверяем, что классы доступны
        assert TemplateRenderer is not None
        assert SimpleTemplates is not None

        # Создаем временную директорию для тестов
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем тестовый шаблон
            template_file = os.path.join(temp_dir, "test.html")
            with open(template_file, "w") as f:
                f.write("<h1>{title}</h1>")

            # Тестируем SimpleTemplates
            simple_templates = SimpleTemplates(directory=temp_dir)
            rendered = simple_templates.render("test.html", {"title": "Test Title"})
            assert "Test Title" in rendered

    def test_validation_enhancements(self):
        """Тест улучшений валидации"""
        from qakeapi.utils.validation import (
            DataValidator,
            StringValidator,
            IntegerValidator,
            EmailValidator,
            validate_json,
        )

        # Проверяем расширенную валидацию
        validator = DataValidator(
            {
                "email": EmailValidator(),
                "age": IntegerValidator(min_value=0, max_value=150),
                "name": StringValidator(min_length=2, max_length=50),
            }
        )

        # Валидные данные
        valid_data = {"email": "test@example.com", "age": 25, "name": "John Doe"}

        result = validator.validate(valid_data)
        assert result.is_valid

        # Невалидные данные
        invalid_data = {"email": "invalid-email", "age": -5, "name": "J"}

        result = validator.validate(invalid_data)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_request_enhancements(self):
        """Тест улучшений Request"""
        from qakeapi.core.request import Request

        # Создаем mock scope
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "query_string": b"param1=value1&param2=value2",
            "headers": [
                (b"content-type", b"application/json"),
                (b"user-agent", b"test-agent"),
            ],
        }

        receive = AsyncMock()
        request = Request(scope, receive)

        # Проверяем базовые свойства
        assert request.method == "GET"
        assert request.path == "/test"
        assert request.query_string == "param1=value1&param2=value2"

        # Проверяем query параметры
        assert request.get_query_param("param1") == "value1"
        assert request.get_query_param("param2") == "value2"
        assert request.get_query_param("nonexistent") is None

        # Проверяем заголовки
        assert request.get_header("content-type") == "application/json"
        assert request.get_header("user-agent") == "test-agent"

    def test_response_enhancements(self):
        """Тест улучшений Response"""
        from qakeapi.core.response import (
            JSONResponse,
            HTMLResponse,
            PlainTextResponse,
            RedirectResponse,
            FileResponse,
        )

        # JSON Response
        json_resp = JSONResponse({"message": "test"}, status_code=201)
        assert json_resp.status_code == 201
        assert json_resp.media_type == "application/json"

        # HTML Response
        html_resp = HTMLResponse("<h1>Test</h1>")
        assert html_resp.media_type == "text/html; charset=utf-8"

        # Plain Text Response
        text_resp = PlainTextResponse("Hello World")
        assert text_resp.media_type == "text/plain; charset=utf-8"

        # Redirect Response
        redirect_resp = RedirectResponse("/new-location")
        assert redirect_resp.status_code == 302  # FOUND по умолчанию
        assert redirect_resp.headers["location"] == "/new-location"


class TestCompatibility:
    """Тесты совместимости"""

    def test_backward_compatibility(self):
        """Тест обратной совместимости"""
        # Проверяем, что старый код продолжает работать
        app = QakeAPI()

        @app.get("/")
        async def root():
            return {"message": "Hello"}

        assert len(app.routes) > 0  # Включая встроенные маршруты

        # Проверяем, что базовые методы доступны
        assert hasattr(app, "get")
        assert hasattr(app, "post")
        assert hasattr(app, "put")
        assert hasattr(app, "delete")
        assert hasattr(app, "patch")

    def test_api_router_compatibility(self):
        """Тест совместимости APIRouter"""
        from qakeapi.core.router import APIRouter

        router = APIRouter()

        @router.get("/test")
        async def test_route():
            return {"test": True}

        assert len(router.routes) == 1

        # Включаем в приложение
        app = QakeAPI()
        app.include_router(router, prefix="/api")

        # Проверяем, что маршрут добавлен
        api_routes = [r for r in app.routes if "/api" in r.path]
        assert len(api_routes) >= 1


@pytest.mark.asyncio
async def test_full_request_cycle():
    """Тест полного цикла запроса"""
    app = QakeAPI()

    @app.get("/full-test")
    async def full_test():
        return {"status": "success", "message": "Full cycle test"}

    # Создаем полный ASGI запрос
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/full-test",
        "query_string": b"",
        "headers": [(b"accept", b"application/json"), (b"user-agent", b"test-client")],
    }

    receive = AsyncMock()
    send = AsyncMock()

    # Выполняем запрос
    await app(scope, receive, send)

    # Проверяем, что send был вызван правильно
    assert send.call_count >= 2

    # Проверяем response.start
    start_call = send.call_args_list[0][0][0]
    assert start_call["type"] == "http.response.start"
    assert start_call["status"] == 200

    # Проверяем response.body
    body_call = send.call_args_list[1][0][0]
    assert body_call["type"] == "http.response.body"
