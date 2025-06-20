import pytest
from qakeapi.security.authentication import BasicAuthBackend, User
from qakeapi.security.authorization import (
    IsAuthenticated,
    IsAdmin,
    RolePermission,
    AuthorizationError,
    requires_auth,
)
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response
import base64
from qakeapi.security.cors import CORSMiddleware
from qakeapi.security.csrf import CSRFMiddleware

@pytest.fixture
def auth_backend():
    backend = BasicAuthBackend()
    backend.add_user("test_user", "test_pass", ["user"])
    backend.add_user("admin", "admin_pass", ["admin", "user"])
    return backend

@pytest.fixture
def mock_request():
    async def create_request(auth_header: str = None):
        headers = {"Authorization": auth_header} if auth_header else {}
        return Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/test",
                "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
            }
        )
    return create_request

@pytest.fixture
def cors_middleware():
    return CORSMiddleware(
        allow_origins=["http://localhost:3000"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Custom-Header"],
        allow_credentials=True
    )

@pytest.fixture
def csrf_middleware():
    return CSRFMiddleware(
        secret_key="test_secret_key",
        safe_methods=["GET", "HEAD", "OPTIONS"],
        token_field_name="csrf_token",
        cookie_name="csrf_token"
    )

@pytest.mark.asyncio
async def test_basic_auth_success(auth_backend):
    credentials = {"username": "test_user", "password": "test_pass"}
    user = await auth_backend.authenticate(credentials)
    assert user is not None
    assert user.username == "test_user"
    assert user.roles == ["user"]

@pytest.mark.asyncio
async def test_basic_auth_wrong_password(auth_backend):
    credentials = {"username": "test_user", "password": "wrong_pass"}
    user = await auth_backend.authenticate(credentials)
    assert user is None

@pytest.mark.asyncio
async def test_basic_auth_nonexistent_user(auth_backend):
    credentials = {"username": "nonexistent", "password": "test_pass"}
    user = await auth_backend.authenticate(credentials)
    assert user is None

@pytest.mark.asyncio
async def test_get_user_success(auth_backend):
    user = await auth_backend.get_user("admin")
    assert user is not None
    assert user.username == "admin"
    assert set(user.roles) == {"admin", "user"}

@pytest.mark.asyncio
async def test_get_user_nonexistent(auth_backend):
    user = await auth_backend.get_user("nonexistent")
    assert user is None

@pytest.mark.asyncio
async def test_is_authenticated_permission():
    permission = IsAuthenticated()
    user = User(username="test", roles=["user"])
    assert await permission.has_permission(user)
    assert not await permission.has_permission(None)

@pytest.mark.asyncio
async def test_is_admin_permission():
    permission = IsAdmin()
    admin = User(username="admin", roles=["admin"])
    user = User(username="user", roles=["user"])
    assert await permission.has_permission(admin)
    assert not await permission.has_permission(user)

@pytest.mark.asyncio
async def test_role_permission():
    permission = RolePermission(["editor"])
    editor = User(username="editor", roles=["editor"])
    user = User(username="user", roles=["user"])
    assert await permission.has_permission(editor)
    assert not await permission.has_permission(user)

@pytest.mark.asyncio
async def test_requires_auth_decorator():
    @requires_auth(IsAuthenticated())
    async def protected_handler(request: Request) -> Response:
        return Response.text("Success")

    request = Request(scope={"type": "http", "method": "GET", "path": "/test"})
    request.user = User(username="test", roles=["user"])
    response = await protected_handler(request)
    assert response.status_code == 200
    assert await response.body == b"Success"

    request.user = None
    response = await protected_handler(request)
    assert response.status_code == 401

async def test_cors_preflight_request(cors_middleware):
    # Создаем тестовый preflight запрос
    request = Request({
        "type": "http",
        "method": "OPTIONS",
        "headers": [
            (b"origin", b"http://localhost:3000"),
            (b"access-control-request-method", b"POST"),
            (b"access-control-request-headers", b"content-type")
        ]
    }, b"")

    async def handler(request):
        return Response.json({"message": "success"})

    response = await cors_middleware(request, handler)
    
    assert response.status_code == 200
    assert (b"access-control-allow-origin", b"http://localhost:3000") in response.headers
    assert (b"access-control-allow-credentials", b"true") in response.headers

async def test_cors_actual_request(cors_middleware):
    # Создаем тестовый запрос
    request = Request({
        "type": "http",
        "method": "GET",
        "headers": [(b"origin", b"http://localhost:3000")]
    }, b"")

    async def handler(request):
        return Response.json({"message": "success"})

    response = await cors_middleware(request, handler)
    
    assert response.status_code == 200
    assert (b"access-control-allow-origin", b"http://localhost:3000") in response.headers
    assert (b"access-control-allow-credentials", b"true") in response.headers

async def test_cors_disallowed_origin(cors_middleware):
    # Создаем тестовый запрос с неразрешенным origin
    request = Request({
        "type": "http",
        "method": "OPTIONS",
        "headers": [(b"origin", b"http://evil.com")]
    }, b"")

    async def handler(request):
        return Response.json({"message": "success"})

    response = await cors_middleware(request, handler)
    
    assert response.status_code == 403

async def test_csrf_safe_method(csrf_middleware):
    # Тестируем безопасный метод (GET)
    request = Request({
        "type": "http",
        "method": "GET",
        "headers": []
    }, b"")

    async def handler(request):
        return Response.json({"message": "success"})

    response = await csrf_middleware(request, handler)
    
    assert response.status_code == 200
    assert any(header[0] == b"set-cookie" for header in response.headers)

async def test_csrf_unsafe_method_without_token(csrf_middleware):
    # Тестируем небезопасный метод без CSRF токена
    request = Request({
        "type": "http",
        "method": "POST",
        "headers": []
    }, b"")

    async def handler(request):
        return Response.json({"message": "success"})

    response = await csrf_middleware(request, handler)
    body = await response.body
    
    assert response.status_code == 403
    assert b'{"detail": "CSRF token missing or invalid"}' in body

async def test_csrf_unsafe_method_with_valid_token(csrf_middleware):
    # Тестируем небезопасный метод с валидным CSRF токеном
    token = "valid_token"
    request = Request({
        "type": "http",
        "method": "POST",
        "headers": [
            (b"x-csrf-token", token.encode()),
            (b"cookie", f"csrf_token={token}".encode())
        ],
        "cookies": {"csrf_token": token}
    }, b"")

    async def handler(request):
        return Response.json({"message": "success"})

    response = await csrf_middleware(request, handler)
    
    # Проверяем, что токен в куках совпадает с токеном в заголовке
    cookie_token = request.cookies.get("csrf_token").value
    header_token = request.headers.get(b"x-csrf-token", b"").decode()
    
    assert cookie_token == header_token
    assert response.status_code == 200 