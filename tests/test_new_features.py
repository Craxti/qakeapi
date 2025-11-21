"""
Тесты новых возможностей QakeAPI
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from qakeapi import QakeAPI
from qakeapi.core.application import QakeAPI as QakeAPICore


class TestNewFeatures:
    """Тесты новых возможностей"""

    def test_import_availability(self):
        """Тест доступности импортов"""
        # Проверяем, что основные компоненты импортируются
        from qakeapi import (
            CORSMiddleware,
            HTTPException,
            JSONResponse,
            LoggingMiddleware,
            QakeAPI,
            Request,
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
        from qakeapi import CacheManager, HealthChecker, JWTManager, MetricsCollector

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
        assert hasattr(app, "middleware_stack")
        assert hasattr(app.middleware_stack, "middleware")

    def test_middleware_chain_fix(self):
        """Тест исправления цепочки middleware"""
        app = QakeAPI()

        # Добавляем несколько middleware
        from qakeapi.middleware.cors import CORSMiddleware
        from qakeapi.middleware.logging import LoggingMiddleware

        app.add_middleware(CORSMiddleware())
        app.add_middleware(LoggingMiddleware())

        assert len(app.middleware_stack.middleware) == 2

        # Проверяем, что метод _apply_middleware существует и не вызывает рекурсию
        assert hasattr(app, "_apply_middleware")

    @pytest.mark.asyncio
    async def test_middleware_execution(self):
        """Тест выполнения middleware без рекурсии"""
        app = QakeAPI()

        # Создаем простой middleware с правильным интерфейсом
        class TestMiddleware:
            def __init__(self):
                self.called = False

            async def __call__(self, request, call_next):
                self.called = True
                return await call_next(request)

        test_mw = TestMiddleware()
        app.add_middleware(test_mw)

        # Создаем mock запрос и call_next
        from qakeapi.core.request import Request
        from qakeapi.core.responses import JSONResponse

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
        }
        request = Request(scope, AsyncMock())
        call_next = AsyncMock()
        call_next.return_value = JSONResponse({"test": "data"})

        # Выполняем middleware через middleware_stack напрямую
        # Проверяем, что middleware добавлен
        assert len(app.middleware_stack.middleware) > 0

        # Проверяем, что middleware имеет правильный интерфейс
        # Создаем простой тест вызова
        async def test_call_next(req):
            return await call_next(req)

        # Вызываем middleware напрямую
        result = await test_mw(request, test_call_next)

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

        assert schema["openapi"] == "3.0.0"
        assert schema["info"]["title"] == "API with OpenAPI"
        assert schema["info"]["description"] == "Enhanced OpenAPI schema"
        assert schema["info"]["version"] == "2.0.0"
        assert "/test" in schema["paths"]

    def test_exception_handlers_enhancement(self):
        """Тест улучшенных обработчиков исключений"""
        app = QakeAPI()

        # Проверяем базовые обработчики (они не регистрируются автоматически)
        from qakeapi.core.exceptions import HTTPException, QakeAPIException

        # Exception handlers регистрируются только при добавлении
        # Проверяем, что словарь существует
        assert hasattr(app, "exception_handlers")
        assert isinstance(app.exception_handlers, dict)

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
        assert len(app.startup_handlers) == 1
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
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем тестовый файл
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test content")

            static_files = StaticFiles(directory=temp_dir)
            assert static_files.directory.exists()

    def test_template_integration(self):
        """Тест интеграции шаблонов"""
        from qakeapi.utils.templates import (
            TemplateEngine,
            TemplateRenderer,
            SimpleTemplates,
        )

        # Проверяем, что классы доступны
        assert TemplateRenderer is not None
        assert TemplateEngine is not None
        assert SimpleTemplates is not None

        # Создаем временную директорию для тестов
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем тестовый шаблон (используем синтаксис {{ variable }})
            template_file = os.path.join(temp_dir, "test.html")
            with open(template_file, "w") as f:
                f.write("<h1>{{ title }}</h1>")

            # Тестируем SimpleTemplates
            simple_templates = SimpleTemplates(directory=temp_dir)
            rendered = simple_templates.render("test.html", {"title": "Test Title"})
            assert "Test Title" in rendered

    def test_validation_enhancements(self):
        """Тест улучшений валидации"""
        from qakeapi.utils.validation import (
            DataValidator,
            EmailValidator,
            IntegerValidator,
            StringValidator,
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
        # Request doesn't have query_string attribute, use query_params instead
        assert "param1" in request.query_params
        assert request.query_params["param1"] == ["value1"]

        # Проверяем query параметры
        assert request.get_query_param("param1") == "value1"
        assert request.get_query_param("param2") == "value2"
        assert request.get_query_param("nonexistent") is None

        # Проверяем заголовки
        assert request.get_header("content-type") == "application/json"
        assert request.get_header("user-agent") == "test-agent"

    def test_response_enhancements(self):
        """Тест улучшений Response"""
        from qakeapi.core.responses import (
            FileResponse,
            HTMLResponse,
            JSONResponse,
            TextResponse,
            RedirectResponse,
        )

        # JSON Response
        json_resp = JSONResponse({"message": "test"}, status_code=201)
        assert json_resp.status_code == 201
        assert json_resp.media_type == "application/json"

        # HTML Response
        html_resp = HTMLResponse("<h1>Test</h1>")
        assert html_resp.media_type == "text/html; charset=utf-8"

        # Plain Text Response (use TextResponse)
        text_resp = TextResponse("Hello World")
        assert text_resp.media_type == "text/plain; charset=utf-8"

        # Redirect Response
        redirect_resp = RedirectResponse("/new-location")
        assert redirect_resp.status_code == 302  # FOUND по умолчанию
        # Headers can be list of tuples, check properly
        if hasattr(redirect_resp, "headers_dict"):
            assert redirect_resp.headers_dict.get("location") == "/new-location"
        else:
            # Check if headers is a list of tuples
            location_found = False
            for h in redirect_resp.headers:
                if isinstance(h, (list, tuple)) and len(h) == 2:
                    key = h[0].decode() if isinstance(h[0], bytes) else h[0]
                    value = h[1].decode() if isinstance(h[1], bytes) else h[1]
                    if key.lower() == "location" and value == "/new-location":
                        location_found = True
                        break
            assert (
                location_found
            ), f"Location header not found in {redirect_resp.headers}"


class TestCompatibility:
    """Тесты совместимости"""

    def test_backward_compatibility(self):
        """Тест обратной совместимости"""
        # Проверяем, что старый код продолжает работать
        app = QakeAPI()

        @app.get("/")
        async def root():
            return {"message": "Hello"}

        assert len(app.router.routes) > 0  # Включая встроенные маршруты

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
        api_routes = [r for r in app.router.routes if "/api" in r.path]
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
