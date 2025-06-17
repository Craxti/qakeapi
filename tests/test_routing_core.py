import pytest
from qakeapi.core.routing import Route, Router
from qakeapi.core.responses import Response, JSONResponse
from qakeapi.core.requests import Request


async def test_handler(request):
    return JSONResponse({"message": "test"})


def test_route_creation():
    """Test basic route creation"""
    route = Route("/test", test_handler, ["GET"])
    assert route.path == "/test"
    assert route.handler == test_handler
    assert route.methods == ["GET"]
    assert route.name is None
    assert route.type == "http"


def test_route_with_parameters():
    """Test route with path parameters"""
    route = Route("/users/{id}", test_handler, ["GET"])
    match = route.match("/users/123")
    assert match == {"id": "123"}
    
    # Test no match
    assert route.match("/posts/123") is None


def test_route_with_multiple_parameters():
    """Test route with multiple path parameters"""
    route = Route("/users/{user_id}/posts/{post_id}", test_handler, ["GET"])
    match = route.match("/users/123/posts/456")
    assert match == {"user_id": "123", "post_id": "456"}


@pytest.mark.asyncio
async def test_router_basic_routing():
    """Test basic routing functionality"""
    router = Router()
    router.add_route("/test", test_handler, ["GET"])
    
    # Test successful route
    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [],
        "query_string": b"",
    })
    response = await router.handle_request(request)
    assert response.status_code == 200
    
    # Test 404
    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/nonexistent",
        "headers": [],
        "query_string": b"",
    })
    response = await router.handle_request(request)
    assert response.status_code == 404


def test_router_url_generation():
    """Test URL generation for named routes"""
    router = Router()
    router.add_route("/users/{id}", test_handler, ["GET"], name="user_detail")
    
    url = router.url_for("user_detail", id=123)
    assert url == "/users/123"
    
    with pytest.raises(ValueError):
        router.url_for("nonexistent")


@pytest.mark.asyncio
async def test_router_middleware():
    """Test middleware functionality"""
    router = Router()
    
    async def test_middleware(handler):
        async def wrapped(request):
            request.middleware_called = True
            return await handler(request)
        return wrapped
    
    router.add_middleware(test_middleware)
    router.add_route("/test", test_handler, ["GET"])
    
    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [],
        "query_string": b"",
    })
    
    response = await router.handle_request(request)
    assert response.status_code == 200
    assert hasattr(request, "middleware_called")
    assert request.middleware_called is True


@pytest.mark.asyncio
async def test_router_websocket_route():
    """Test WebSocket route addition"""
    router = Router()
    
    async def ws_handler(websocket):
        pass
    
    router.add_route("/ws", ws_handler, ["GET"], route_type="websocket")
    
    route = router.find_route("/ws", type="websocket")
    assert route is not None
    assert route.type == "websocket"
    assert route.path == "/ws"


def test_route_pattern_compilation():
    """Test route pattern compilation"""
    route = Route("/users/{id}", test_handler, ["GET"])
    
    # Test basic match
    match = route.match("/users/123")
    assert match == {"id": "123"}
    
    # Test no match
    assert route.match("/posts/123") is None


def test_router_methods():
    """Test router method handling"""
    router = Router()
    router.add_route("/test", test_handler, ["GET", "POST"])
    
    route = router.find_route("/test")
    assert route is not None
    assert "GET" in route.methods
    assert "POST" in route.methods 