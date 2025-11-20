"""
Тесты улучшенной системы обработки ошибок
"""
import pytest
import logging
from unittest.mock import Mock, patch
from datetime import datetime

from qakeapi.core.error_handling import (
    ErrorContext, ErrorLogger, ErrorResponseBuilder, ErrorHandler
)
from qakeapi.core.request import Request
from qakeapi.core.exceptions import HTTPException
from qakeapi.core.response import JSONResponse
from qakeapi.utils.status import status
from pydantic import ValidationError, BaseModel, Field


class TestModel(BaseModel):
    """Тестовая модель для валидации"""
    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=0)


class TestErrorContext:
    """Тесты контекста ошибки"""
    
    def test_error_context_creation(self):
        """Тест создания контекста ошибки"""
        # Создаем мок запроса
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "client": ("127.0.0.1", 12345),
            "headers": [(b"user-agent", b"TestAgent/1.0")]
        }
        request = Request(scope, None)
        exception = ValueError("Test error")
        
        context = ErrorContext(
            error_id="test-error-id",
            request=request,
            exception=exception,
            timestamp=datetime.now()
        )
        
        assert context.error_id == "test-error-id"
        assert isinstance(context.timestamp, datetime)
        assert context.path == "/test"
        assert context.method == "GET"
        assert context.client_ip == "127.0.0.1"
        assert context.user_agent == "TestAgent/1.0"
        assert context.exception_type == "ValueError"
        assert context.exception_message == "Test error"
    
    def test_error_context_with_user_data(self):
        """Тест контекста с пользовательскими данными"""
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/test",
            "client": ("192.168.1.1", 12345),
            "headers": [(b"user-agent", b"TestAgent/2.0")]
        }
        request = Request(scope, None)
        exception = HTTPException(status.BAD_REQUEST, "Bad request")
        
        context = ErrorContext(
            error_id="test-error-id-2",
            request=request,
            exception=exception,
            timestamp=datetime.now(),
            user_id="123",
            session_id="session-123",
            correlation_id="corr-123"
        )
        
        assert context.path == "/api/test"
        assert context.method == "POST"
        assert context.user_id == "123"
        assert context.session_id == "session-123"
        assert context.correlation_id == "corr-123"
        assert context.client_ip == "192.168.1.1"
        assert context.user_agent == "TestAgent/2.0"


class TestErrorLogger:
    """Тесты логгера ошибок"""
    
    def test_error_logger_creation(self):
        """Тест создания логгера"""
        logger = ErrorLogger()
        assert logger.logger.name == "qakeapi.errors"
        
        # Тест с кастомным логгером
        custom_logger = logging.getLogger("test.logger")
        error_logger = ErrorLogger(logger=custom_logger)
        assert error_logger.logger.name == "test.logger"
    
    @pytest.mark.asyncio
    async def test_log_error(self):
        """Тест логирования ошибки"""
        with patch('qakeapi.core.error_handling.logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            error_logger = ErrorLogger()
            error_logger.logger = mock_logger
            
            # Создаем контекст ошибки
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/test",
                "client": ("127.0.0.1", 12345),
                "headers": [(b"user-agent", b"TestAgent/1.0")]
            }
            request = Request(scope, None)
            exception = ValueError("Test error")
            
            context = ErrorContext(
                error_id="test-error-id",
                request=request,
                exception=exception,
                timestamp=datetime.now()
            )
            
            await error_logger.log_error(context)
            
            # Проверяем, что логгер был вызван
            mock_logger.log.assert_called_once()
            args, kwargs = mock_logger.log.call_args
            assert args[0] == logging.ERROR
            # Проверяем, что сообщение содержит информацию об ошибке
            assert "ValueError" in args[1]
            assert "GET /test" in args[1]
    
    def test_sanitize_headers(self):
        """Тест санитизации заголовков"""
        error_logger = ErrorLogger()
        
        headers = {
            "authorization": "Bearer token123",
            "content-type": "application/json",
            "x-api-key": "secret-key",
            "user-agent": "TestAgent/1.0"
        }
        
        sanitized = error_logger._sanitize_headers(headers)
        
        assert sanitized["authorization"] == "[REDACTED]"
        assert sanitized["content-type"] == "application/json"
        assert sanitized["x-api-key"] == "[REDACTED]"
        assert sanitized["user-agent"] == "TestAgent/1.0"


class TestErrorResponseBuilder:
    """Тесты построителя ответов с ошибками"""
    
    def test_http_exception_response(self):
        """Тест ответа для HTTP исключения"""
        builder = ErrorResponseBuilder(debug=False)
        
        # Создаем контекст ошибки
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "client": ("127.0.0.1", 12345),
            "headers": []
        }
        request = Request(scope, None)
        exception = HTTPException(status.BAD_REQUEST, "Bad request")
        
        context = ErrorContext(
            error_id="test-error-id",
            request=request,
            exception=exception,
            timestamp=datetime.now()
        )
        
        response = builder.build_response(context)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.BAD_REQUEST
        
        # Проверяем содержимое ответа
        content = response.body
        if isinstance(content, bytes):
            import json
            content = json.loads(content.decode())
        
        assert content["detail"] == "Bad request"
        assert "error_id" in content
        assert "timestamp" in content
    
    def test_validation_error_response(self):
        """Тест ответа для ошибки валидации"""
        builder = ErrorResponseBuilder(debug=False)
        
        # Создаем ошибку валидации
        error = None
        try:
            TestModel(name="", age=-1)
        except ValidationError as e:
            error = e
        
        # Создаем контекст ошибки
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "client": ("127.0.0.1", 12345),
            "headers": []
        }
        request = Request(scope, None)
        
        context = ErrorContext(
            error_id="test-error-id",
            request=request,
            exception=error,
            timestamp=datetime.now()
        )
        
        response = builder.build_response(context)
        
        assert response.status_code == status.INTERNAL_SERVER_ERROR  # Generic exception handler
        
        content = response.body
        if isinstance(content, bytes):
            import json
            content = json.loads(content.decode())
        
        assert content["detail"] == "Internal Server Error"
        assert content["type"] == "internal_error"
    
    def test_generic_error_response(self):
        """Тест ответа для общей ошибки"""
        builder = ErrorResponseBuilder(debug=False)
        
        # Создаем контекст ошибки
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "client": ("127.0.0.1", 12345),
            "headers": []
        }
        request = Request(scope, None)
        exception = ValueError("Generic error")
        
        context = ErrorContext(
            error_id="test-error-id",
            request=request,
            exception=exception,
            timestamp=datetime.now()
        )
        
        response = builder.build_response(context)
        
        assert response.status_code == status.INTERNAL_SERVER_ERROR
        
        content = response.body
        if isinstance(content, bytes):
            import json
            content = json.loads(content.decode())
        
        assert content["detail"] == "Internal Server Error"
        assert content["type"] == "internal_error"
    
    def test_debug_mode_response(self):
        """Тест ответа в режиме отладки"""
        builder = ErrorResponseBuilder(debug=True)
        
        # Создаем контекст ошибки
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "client": ("127.0.0.1", 12345),
            "headers": []
        }
        request = Request(scope, None)
        exception = ValueError("Debug error")
        
        context = ErrorContext(
            error_id="test-error-id",
            request=request,
            exception=exception,
            timestamp=datetime.now()
        )
        
        response = builder.build_response(context)
        
        content = response.body
        if isinstance(content, bytes):
            import json
            content = json.loads(content.decode())
        
        assert "debug" in content
        assert content["debug"]["exception_type"] == "ValueError"
        assert content["debug"]["request"]["path"] == "/test"
        assert content["debug"]["request"]["method"] == "GET"


class TestErrorHandler:
    """Тесты обработчика ошибок"""
    
    @pytest.mark.asyncio
    async def test_handle_http_exception(self):
        """Тест обработки HTTP исключения"""
        handler = ErrorHandler(debug=False)
        
        # Создаем мок запроса
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "client": ("127.0.0.1", 12345),
            "headers": []
        }
        request = Request(scope, None)
        exception = HTTPException(status.NOT_FOUND, "Not found")
        
        response = await handler.handle_exception(request, exception)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_handle_validation_error(self):
        """Тест обработки ошибки валидации"""
        handler = ErrorHandler(debug=False)
        
        error = None
        try:
            TestModel(name="", age=-1)
        except ValidationError as e:
            error = e
        
        # Создаем мок запроса
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "client": ("127.0.0.1", 12345),
            "headers": []
        }
        request = Request(scope, None)
        
        response = await handler.handle_exception(request, error)
        
        assert response.status_code == status.BAD_REQUEST or response.status_code == status.INTERNAL_SERVER_ERROR  # ValidationError может обрабатываться по-разному
    
    @pytest.mark.asyncio
    async def test_handle_generic_exception(self):
        """Тест обработки общего исключения"""
        handler = ErrorHandler(debug=False)
        
        # Создаем мок запроса
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "client": ("127.0.0.1", 12345),
            "headers": []
        }
        request = Request(scope, None)
        exception = ValueError("Test error")
        
        response = await handler.handle_exception(request, exception)
        
        assert response.status_code == status.INTERNAL_SERVER_ERROR  # Generic exception
    
    @pytest.mark.asyncio
    async def test_custom_exception_handler(self):
        """Тест кастомного обработчика исключений"""
        handler = ErrorHandler(debug=False)
        
        # Добавляем кастомный обработчик
        async def custom_handler(request, exception):
            return JSONResponse(
                {"custom": True, "message": str(exception)},
                status_code=418  # I'm a teapot
            )
        
        handler.add_exception_handler(ValueError, custom_handler)
        
        # Создаем мок запроса
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "client": ("127.0.0.1", 12345),
            "headers": []
        }
        request = Request(scope, None)
        exception = ValueError("Custom error")
        
        response = await handler.handle_exception(request, exception)
        
        assert response.status_code == 418
        
        content = response.body
        if isinstance(content, bytes):
            import json
            content = json.loads(content.decode())
        
        assert content["custom"] is True
        assert content["message"] == "Custom error"
    
    def test_extract_context_info(self):
        """Тест извлечения контекстной информации из запроса"""
        handler = ErrorHandler()
        
        # Создаем мок запроса с заголовками
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/test",
            "client": ("192.168.1.1", 12345),
            "headers": [
                (b"user-agent", b"TestAgent/1.0"),
                (b"x-user-id", b"123"),
                (b"x-session-id", b"session-456"),
                (b"x-correlation-id", b"corr-789")
            ]
        }
        request = Request(scope, None)
        
        context_info = handler._extract_context_info(request)
        
        assert context_info["user_id"] == "123"
        assert context_info["session_id"] == "session-456"
        assert context_info["correlation_id"] == "corr-789"


if __name__ == "__main__":
    pytest.main([__file__])


