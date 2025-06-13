import pytest
from qakeapi.core.middleware.cors import CORSConfig, CORSMiddleware
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response

@pytest.fixture
def cors_config():
    return CORSConfig(
        allow_origins=["http://localhost:3000"],
        allow_methods=["GET", "POST"],
        allow_headers=["X-Custom-Header"],
        allow_credentials=True,
        expose_headers=["X-Custom-Header"],
        max_age=3600
    )

@pytest.fixture
def default_cors_middleware():
    return CORSMiddleware()

@pytest.fixture
def custom_cors_middleware(cors_config):
    return CORSMiddleware(cors_config)

async def mock_handler(request):
    return Response(content={"message": "success"})

@pytest.mark.asyncio
async def test_cors_preflight_default_config(default_cors_middleware):
    request = Request({
        "type": "http",
        "method": "OPTIONS",
        "headers": [
            (b"origin", b"http://example.com"),
            (b"access-control-request-method", b"POST"),
            (b"access-control-request-headers", b"content-type")
        ]
    })
    
    response = await default_cors_middleware(request, mock_handler)
    assert response.status_code == 200
    
    headers = dict(response.headers)
    assert headers[b"Access-Control-Allow-Origin"] == b"http://example.com"
    assert b"GET" in headers[b"Access-Control-Allow-Methods"]
    assert b"POST" in headers[b"Access-Control-Allow-Methods"]

@pytest.mark.asyncio
async def test_cors_preflight_custom_config(custom_cors_middleware):
    request = Request({
        "type": "http",
        "method": "OPTIONS",
        "headers": [
            (b"origin", b"http://localhost:3000"),
            (b"access-control-request-method", b"POST"),
            (b"access-control-request-headers", b"X-Custom-Header")
        ]
    })
    
    response = await custom_cors_middleware(request, mock_handler)
    assert response.status_code == 200
    
    headers = dict(response.headers)
    assert headers[b"Access-Control-Allow-Origin"] == b"http://localhost:3000"
    assert b"GET, POST" == headers[b"Access-Control-Allow-Methods"]
    assert headers[b"Access-Control-Allow-Headers"] == b"X-Custom-Header"
    assert headers[b"Access-Control-Allow-Credentials"] == b"true"
    assert headers[b"Access-Control-Max-Age"] == b"3600"

@pytest.mark.asyncio
async def test_cors_actual_request(custom_cors_middleware):
    request = Request({
        "type": "http",
        "method": "GET",
        "headers": [(b"origin", b"http://localhost:3000")]
    })
    
    response = await custom_cors_middleware(request, mock_handler)
    assert response.status_code == 200
    
    headers = dict(response.headers)
    assert headers[b"Access-Control-Allow-Origin"] == b"http://localhost:3000"
    assert headers[b"Access-Control-Allow-Credentials"] == b"true"
    assert headers[b"Access-Control-Expose-Headers"] == b"X-Custom-Header"

@pytest.mark.asyncio
async def test_cors_disallowed_origin(custom_cors_middleware):
    request = Request({
        "type": "http",
        "method": "OPTIONS",
        "headers": [
            (b"origin", b"http://evil.com"),
            (b"access-control-request-method", b"POST")
        ]
    })
    
    response = await custom_cors_middleware(request, mock_handler)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_cors_no_origin(custom_cors_middleware):
    request = Request({
        "type": "http",
        "method": "GET",
        "headers": []
    })
    
    response = await custom_cors_middleware(request, mock_handler)
    assert response.status_code == 200
    assert not any(h[0] == b"Access-Control-Allow-Origin" for h in response.headers) 