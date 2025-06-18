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


def get_header_value(headers, name):
    """Helper function to get header value from list of tuples"""
    for k, v in headers:
        if k.decode().lower() == name.lower():
            return v.decode()
    return None


@pytest.mark.asyncio
async def test_base_middleware():
    middleware = Middleware()
    request = MockRequest()
    response = await middleware(request, mock_call_next)
    assert isinstance(response, Response)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_cors_middleware_default():
    config = CORSConfig(allow_origins=["*"])
    middleware = CORSMiddleware(config)
    request = MockRequest(headers={b"origin": b"http://example.com"})
    response = await middleware(request, mock_call_next)
    assert get_header_value(response.headers, "Access-Control-Allow-Origin") == "http://example.com"


@pytest.mark.asyncio
async def test_cors_middleware_specific_origin():
    config = CORSConfig(allow_origins=["http://example.com"])
    middleware = CORSMiddleware(config)
    request = MockRequest(headers={b"origin": b"http://example.com"})
    response = await middleware(request, mock_call_next)
    assert get_header_value(response.headers, "Access-Control-Allow-Origin") == "http://example.com"


@pytest.mark.asyncio
async def test_cors_middleware_options():
    config = CORSConfig(
        allow_origins=["http://example.com"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        max_age=3600
    )
    middleware = CORSMiddleware(config)
    request = MockRequest(method="OPTIONS", headers={b"origin": b"http://example.com"})
    response = await middleware(request, mock_call_next)
    assert get_header_value(response.headers, "Access-Control-Allow-Methods") == "GET, POST"
    assert get_header_value(response.headers, "Access-Control-Allow-Headers") == "Content-Type"
    assert get_header_value(response.headers, "Access-Control-Max-Age") == "3600"


@pytest.mark.asyncio
async def test_request_logging_middleware(capsys):
    middleware = RequestLoggingMiddleware()
    request = MockRequest(method="GET", path="/test")
    response = await middleware(request, mock_call_next)
    captured = capsys.readouterr()
    assert "GET /test" in captured.out
    assert "200" in captured.out


@pytest.mark.asyncio
async def test_error_handling_middleware():
    async def failing_call_next(request):
        raise ValueError("Test error")

    middleware = ErrorHandlingMiddleware()
    request = MockRequest()
    response = await middleware(request, failing_call_next)
    assert response.status_code == 500
    body = await response.body
    assert body == b'{"detail": "Test error", "type": "ValueError"}'


@pytest.mark.asyncio
async def test_authentication_middleware_no_header():
    middleware = AuthenticationMiddleware()
    request = MockRequest()
    response = await middleware(request, mock_call_next)
    assert response.status_code == 401
    body = await response.body
    assert b"Not authenticated" in body


@pytest.mark.asyncio
async def test_authentication_middleware_invalid_scheme():
    middleware = AuthenticationMiddleware(auth_scheme="Bearer")
    request = MockRequest(headers={b"authorization": b"Basic token123"})
    response = await middleware(request, mock_call_next)
    assert response.status_code == 401
    body = await response.body
    assert b"Invalid authentication scheme" in body


@pytest.mark.asyncio
async def test_authentication_middleware_valid():
    middleware = AuthenticationMiddleware()
    request = MockRequest(headers={b"authorization": b"Bearer token123"})
    response = await middleware(request, mock_call_next)
    assert response.status_code == 200
    assert hasattr(request, "auth_token")
    assert request.auth_token == "token123"


@pytest.mark.asyncio
async def test_authentication_middleware_exempt_path():
    middleware = AuthenticationMiddleware(exempt_paths=["/public"])
    request = MockRequest(path="/public")
    response = await middleware(request, mock_call_next)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_middleware():
    middleware = RateLimitMiddleware(requests_per_minute=2, window_size=60)
    request = MockRequest()
    
    # First request should succeed
    response1 = await middleware(request, mock_call_next)
    assert response1.status_code == 200
    
    # Second request should succeed
    response2 = await middleware(request, mock_call_next)
    assert response2.status_code == 200
    
    # Third request should be rate limited
    response3 = await middleware(request, mock_call_next)
    assert response3.status_code == 429
    body = await response3.body
    assert b"Too many requests" in body


@pytest.mark.asyncio
async def test_rate_limit_middleware_window():
    middleware = RateLimitMiddleware(requests_per_minute=1, window_size=1)
    request = MockRequest()
    
    # First request should succeed
    response1 = await middleware(request, mock_call_next)
    assert response1.status_code == 200
    
    # Wait for window to expire
    time.sleep(1.1)
    
    # Next request should succeed
    response2 = await middleware(request, mock_call_next)
    assert response2.status_code == 200 