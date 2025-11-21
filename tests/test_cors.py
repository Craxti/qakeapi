import pytest

from qakeapi.core.middleware.cors import CORSConfig, CORSMiddleware
from qakeapi.core.request import Request
from qakeapi.core.responses import Response


@pytest.fixture
def cors_config():
    return CORSConfig(
        allow_origins=["http://localhost:3000"],
        allow_methods=["GET", "POST"],
        allow_headers=["X-Custom-Header"],
        allow_credentials=True,
        expose_headers=["X-Custom-Header"],
        max_age=3600,
    )


@pytest.fixture
def default_cors_middleware():
    return CORSMiddleware()


@pytest.fixture
def custom_cors_middleware(cors_config):
    return CORSMiddleware(cors_config)


async def mock_receive():
    return {"type": "http.request", "body": b"", "more_body": False}


async def mock_handler(request):
    return Response(content={"message": "success"})


@pytest.mark.asyncio
async def test_cors_preflight_default_config(default_cors_middleware):
    request = Request(
        {
            "type": "http",
            "method": "OPTIONS",
            "headers": [
                (b"origin", b"http://example.com"),
                (b"access-control-request-method", b"POST"),
                (b"access-control-request-headers", b"content-type"),
            ],
        },
        mock_receive,
    )

    response = await default_cors_middleware(request, mock_handler)
    assert response.status_code == 200

    # Преобразуем headers в словарь для удобства проверки
    headers_dict = {}
    for key, value in response.headers:
        key_str = key.decode() if isinstance(key, bytes) else key
        headers_dict[key_str.lower()] = value.decode() if isinstance(value, bytes) else value
    
    assert headers_dict.get("access-control-allow-origin") == "http://example.com"
    methods = headers_dict.get("access-control-allow-methods", "")
    assert "GET" in methods
    assert "POST" in methods


@pytest.mark.asyncio
async def test_cors_preflight_custom_config(custom_cors_middleware):
    request = Request(
        {
            "type": "http",
            "method": "OPTIONS",
            "headers": [
                (b"origin", b"http://localhost:3000"),
                (b"access-control-request-method", b"POST"),
                (b"access-control-request-headers", b"X-Custom-Header"),
            ],
        },
        mock_receive,
    )

    response = await custom_cors_middleware(request, mock_handler)
    assert response.status_code == 200

    # Преобразуем headers в словарь для удобства проверки
    headers_dict = {}
    for key, value in response.headers:
        key_str = key.decode() if isinstance(key, bytes) else key
        headers_dict[key_str.lower()] = value.decode() if isinstance(value, bytes) else value
    
    assert headers_dict.get("access-control-allow-origin") == "http://localhost:3000"
    assert headers_dict.get("access-control-allow-methods") == "GET, POST"
    assert headers_dict.get("access-control-allow-headers") == "X-Custom-Header"
    assert headers_dict.get("access-control-allow-credentials") == "true"
    assert headers_dict.get("access-control-max-age") == "3600"


@pytest.mark.asyncio
async def test_cors_actual_request(custom_cors_middleware):
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "headers": [(b"origin", b"http://localhost:3000")],
        },
        mock_receive,
    )

    response = await custom_cors_middleware(request, mock_handler)
    assert response.status_code == 200

    # Преобразуем headers в словарь для удобства проверки
    headers_dict = {}
    for key, value in response.headers:
        key_str = key.decode() if isinstance(key, bytes) else key
        headers_dict[key_str.lower()] = value.decode() if isinstance(value, bytes) else value
    
    assert headers_dict.get("access-control-allow-origin") == "http://localhost:3000"
    assert headers_dict.get("access-control-allow-credentials") == "true"
    assert headers_dict.get("access-control-expose-headers") == "X-Custom-Header"


@pytest.mark.asyncio
async def test_cors_disallowed_origin(custom_cors_middleware):
    request = Request(
        {
            "type": "http",
            "method": "OPTIONS",
            "headers": [
                (b"origin", b"http://evil.com"),
                (b"access-control-request-method", b"POST"),
            ],
        },
        mock_receive,
    )

    response = await custom_cors_middleware(request, mock_handler)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cors_no_origin(custom_cors_middleware):
    request = Request(
        {"type": "http", "method": "GET", "headers": []}, mock_receive
    )

    response = await custom_cors_middleware(request, mock_handler)
    assert response.status_code == 200
    assert not any(h[0] == b"Access-Control-Allow-Origin" for h in response.headers)
