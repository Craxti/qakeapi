import time
import pytest
from qakeapi.core.middleware import (
    Middleware,
    CORSMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware,
    AuthenticationMiddleware,
    RateLimitMiddleware,
)
from qakeapi.core.middleware.cors import CORSConfig
from qakeapi.core.requests import Request
from qakeapi.core.responses import JSONResponse, Response


class MockRequest:
    def __init__(self, method="GET", path="/", headers=None, client_ip="127.0.0.1"):
        self.method = method
        self.path = path
        self.headers = headers or {}
        self._client_ip = client_ip
        self.scope = {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [(k.lower(), v) for k, v in headers.items()] if headers else []
        }

    def client(self):
        return (self._client_ip, 1234)


async def mock_call_next(request):
    return Response(content={"message": "test"})


def get_header_value(headers, header_name):
    """Helper function to get header value from list of tuples"""
    header_name_bytes = header_name.encode() if isinstance(header_name, str) else header_name
    for key, value in headers:
        if key.lower() == header_name_bytes.lower():
            return value.decode()
    return None


@pytest.fixture
def mock_request():
    return Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [(b"host", b"testserver")],
            "client": ("127.0.0.1", 8000)
        }
    )


@pytest.fixture
def mock_response():
    return Response(content="Test response")


@pytest.fixture
async def mock_handler(mock_response):
    async def handler(request):
        return mock_response
    return handler


async def test_base_middleware(mock_request, mock_handler):
    middleware = Middleware()
    response = await middleware(mock_request, mock_handler)
    assert isinstance(response, Response)
    body = await response.body
    assert body == b"Test response"


@pytest.mark.parametrize("origin,expected_origin", [
    ("http://localhost:3000", "http://localhost:3000"),
    ("http://example.com", None),
])
async def test_cors_middleware(mock_request, mock_handler, origin, expected_origin):
    config = CORSConfig(
        allow_origins=["http://localhost:3000"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        allow_credentials=True
    )
    middleware = CORSMiddleware(config)
    
    if origin:
        mock_request.scope["headers"].append((b"origin", origin.encode()))
    
    response = await middleware(mock_request, mock_handler)
    
    if expected_origin:
        assert get_header_value(response.headers, "Access-Control-Allow-Origin") == expected_origin
        assert get_header_value(response.headers, "Access-Control-Allow-Credentials") == "true"
    else:
        assert not any(key == b"Access-Control-Allow-Origin" for key, _ in response.headers)


async def test_cors_middleware_options(mock_request, mock_handler):
    config = CORSConfig(
        allow_origins=["http://localhost:3000"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"]
    )
    middleware = CORSMiddleware(config)
    
    mock_request.scope["method"] = "OPTIONS"
    mock_request.scope["headers"].append((b"origin", b"http://localhost:3000"))
    
    response = await middleware(mock_request, mock_handler)
    
    assert get_header_value(response.headers, "Access-Control-Allow-Methods") == "GET, POST"
    assert get_header_value(response.headers, "Access-Control-Allow-Headers") == "Content-Type"


async def test_request_logging_middleware(mock_request, mock_handler, capsys):
    middleware = RequestLoggingMiddleware()
    response = await middleware(mock_request, mock_handler)
    
    captured = capsys.readouterr()
    assert "GET /test" in captured.out
    assert "200" in captured.out


async def test_error_handling_middleware_success(mock_request, mock_handler):
    middleware = ErrorHandlingMiddleware()
    response = await middleware(mock_request, mock_handler)
    assert response.status_code == 200


async def test_error_handling_middleware_error(mock_request):
    async def error_handler(request):
        raise ValueError("Test error")
    
    middleware = ErrorHandlingMiddleware()
    response = await middleware(mock_request, error_handler)
    
    assert response.status_code == 500
    body = await response.body
    assert b"Test error" in body


@pytest.mark.parametrize("auth_header,expected_status", [
    ("Bearer valid-token", 200),
    ("Basic invalid-scheme", 401),
    (None, 401),
])
async def test_authentication_middleware(mock_request, mock_handler, auth_header, expected_status):
    middleware = AuthenticationMiddleware(auth_scheme="Bearer")
    
    if auth_header:
        mock_request.scope["headers"].append((b"authorization", auth_header.encode()))
    
    response = await middleware(mock_request, mock_handler)
    assert response.status_code == expected_status
    
    if expected_status == 200:
        assert hasattr(mock_request, "auth_token")
        assert mock_request.auth_token == "valid-token"


async def test_authentication_middleware_exempt_path(mock_request, mock_handler):
    middleware = AuthenticationMiddleware(exempt_paths=["/test"])
    response = await middleware(mock_request, mock_handler)
    assert response.status_code == 200


async def test_rate_limit_middleware_within_limit(mock_request, mock_handler):
    middleware = RateLimitMiddleware(requests_per_minute=2)
    
    # Первый запрос
    response1 = await middleware(mock_request, mock_handler)
    assert response1.status_code == 200
    
    # Второй запрос
    response2 = await middleware(mock_request, mock_handler)
    assert response2.status_code == 200


async def test_rate_limit_middleware_exceeds_limit(mock_request, mock_handler):
    middleware = RateLimitMiddleware(requests_per_minute=1)
    
    # Первый запрос
    await middleware(mock_request, mock_handler)
    
    # Второй запрос (должен быть отклонен)
    response = await middleware(mock_request, mock_handler)
    assert response.status_code == 429
    body = await response.body
    assert b"Too many requests" in body


async def test_rate_limit_middleware_window_cleanup(mock_request, mock_handler):
    middleware = RateLimitMiddleware(requests_per_minute=1, window_size=1)
    
    # Первый запрос
    await middleware(mock_request, mock_handler)
    
    # Ждем, пока окно очистится
    time.sleep(1.1)
    
    # Следующий запрос должен пройти
    response = await middleware(mock_request, mock_handler)
    assert response.status_code == 200


# Дополнительные тесты CORS middleware
async def test_cors_middleware_wildcard_origin(mock_request, mock_handler):
    config = CORSConfig(
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        expose_headers=["X-Custom-Header"]
    )
    middleware = CORSMiddleware(config)
    
    mock_request.scope["headers"].append((b"origin", b"http://any-origin.com"))
    
    response = await middleware(mock_request, mock_handler)
    assert get_header_value(response.headers, "Access-Control-Allow-Origin") == "http://any-origin.com"
    assert get_header_value(response.headers, "Access-Control-Expose-Headers") == "X-Custom-Header"


async def test_cors_middleware_no_origin(mock_request, mock_handler):
    config = CORSConfig(
        allow_origins=["http://localhost:3000"],
        allow_methods=["GET", "POST"]
    )
    middleware = CORSMiddleware(config)
    
    response = await middleware(mock_request, mock_handler)
    assert not any(key == b"Access-Control-Allow-Origin" for key, _ in response.headers)


async def test_cors_middleware_options_no_origin(mock_request, mock_handler):
    config = CORSConfig(
        allow_origins=["http://localhost:3000"],
        allow_methods=["GET", "POST"]
    )
    middleware = CORSMiddleware(config)
    
    mock_request.scope["method"] = "OPTIONS"
    
    response = await middleware(mock_request, mock_handler)
    assert response.status_code == 400
    body = await response.body
    assert b"No origin header" in body


async def test_cors_middleware_options_invalid_origin(mock_request, mock_handler):
    config = CORSConfig(
        allow_origins=["http://localhost:3000"],
        allow_methods=["GET", "POST"]
    )
    middleware = CORSMiddleware(config)
    
    mock_request.scope["method"] = "OPTIONS"
    mock_request.scope["headers"].append((b"origin", b"http://invalid-origin.com"))
    
    response = await middleware(mock_request, mock_handler)
    assert response.status_code == 400
    body = await response.body
    assert b"Origin not allowed" in body


async def test_cors_middleware_default_config(mock_request, mock_handler):
    middleware = CORSMiddleware()  # Используем конфигурацию по умолчанию
    
    mock_request.scope["headers"].append((b"origin", b"http://any-origin.com"))
    
    response = await middleware(mock_request, mock_handler)
    assert get_header_value(response.headers, "Access-Control-Allow-Origin") == "http://any-origin.com"
    
    # Проверяем, что все методы разрешены по умолчанию
    mock_request.scope["method"] = "OPTIONS"
    response = await middleware(mock_request, mock_handler)
    allowed_methods = get_header_value(response.headers, "Access-Control-Allow-Methods")
    assert "GET" in allowed_methods
    assert "POST" in allowed_methods
    assert "PUT" in allowed_methods
    assert "DELETE" in allowed_methods
    assert "OPTIONS" in allowed_methods
    assert "PATCH" in allowed_methods


# Дополнительные тесты для ErrorHandlingMiddleware
async def test_error_handling_middleware_custom_exception(mock_request):
    class CustomError(Exception):
        pass

    async def error_handler(request):
        raise CustomError("Custom test error")
    
    middleware = ErrorHandlingMiddleware()
    response = await middleware(mock_request, error_handler)
    
    assert response.status_code == 500
    body = await response.body
    assert b"Custom test error" in body
    assert b"CustomError" in body


# Дополнительные тесты для RateLimitMiddleware
async def test_rate_limit_middleware_unknown_client(mock_request, mock_handler):
    middleware = RateLimitMiddleware(requests_per_minute=2)
    
    # Удаляем информацию о клиенте
    mock_request.scope["client"] = None
    
    response = await middleware(mock_request, mock_handler)
    assert response.status_code == 200
    assert "unknown" in middleware.requests


async def test_rate_limit_middleware_cleanup(mock_request, mock_handler):
    middleware = RateLimitMiddleware(requests_per_minute=2, window_size=0.1)
    client = mock_request.client[0]
    
    # Первый запрос
    await middleware(mock_request, mock_handler)
    assert len(middleware.requests[client]) == 1
    
    # Ждем, пока окно очистится
    time.sleep(0.2)
    
    # Второй запрос должен очистить старые
    response = await middleware(mock_request, mock_handler)
    assert response.status_code == 200
    assert len(middleware.requests[client]) == 1 