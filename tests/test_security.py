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
    backend.add_user("testuser", "password123", ["user"])
    backend.add_user("admin", "admin123", ["admin", "user"])
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
async def test_basic_auth_success(auth_backend, mock_request):
    auth_header = f"Basic {base64.b64encode(b'testuser:password123').decode()}"
    request = await mock_request(auth_header)
    
    user = await auth_backend.authenticate(request)
    assert user is not None
    assert user.username == "testuser"
    assert "user" in user.roles

@pytest.mark.asyncio
async def test_basic_auth_failure(auth_backend, mock_request):
    auth_header = f"Basic {base64.b64encode(b'testuser:wrongpass').decode()}"
    request = await mock_request(auth_header)
    
    user = await auth_backend.authenticate(request)
    assert user is None

@pytest.mark.asyncio
async def test_is_authenticated_permission():
    permission = IsAuthenticated()
    user = User(id="1", username="test", is_active=True)
    request = Request(scope={"type": "http", "method": "GET", "path": "/test"})
    
    assert await permission.has_permission(request, user)
    assert not await permission.has_permission(request, None)

@pytest.mark.asyncio
async def test_is_admin_permission():
    permission = IsAdmin()
    admin = User(id="1", username="admin", roles=["admin"])
    user = User(id="2", username="user", roles=["user"])
    request = Request(scope={"type": "http", "method": "GET", "path": "/test"})
    
    assert await permission.has_permission(request, admin)
    assert not await permission.has_permission(request, user)

@pytest.mark.asyncio
async def test_role_permission():
    permission = RolePermission(["editor"])
    editor = User(id="1", username="editor", roles=["editor"])
    user = User(id="2", username="user", roles=["user"])
    request = Request(scope={"type": "http", "method": "GET", "path": "/test"})
    
    assert await permission.has_permission(request, editor)
    assert not await permission.has_permission(request, user)

@pytest.mark.asyncio
async def test_requires_auth_decorator():
    @requires_auth(IsAuthenticated())
    async def protected_handler(request: Request) -> Response:
        return Response.text("Success")
    
    request = Request(scope={"type": "http", "method": "GET", "path": "/test"})
    request.user = User(id="1", username="test", is_active=True)
    
    response = await protected_handler(request)
    assert await response.body == b"Success"
    
    request.user = None
    with pytest.raises(AuthorizationError):
        await protected_handler(request) 