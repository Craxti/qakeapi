import pytest
from qakeapi.security.authentication import BasicAuthBackend, User
from qakeapi.security.authorization import (
    IsAuthenticated, IsAdmin, RolePermission, 
    AuthorizationError, requires_auth
)
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response
import base64

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
                "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()]
            }
        )
    return create_request

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