from typing import Any, Dict

import pytest

from qakeapi.core.requests import Request
from qakeapi.core.responses import Response
from qakeapi.core.routing import HTTPRoute, HTTPRouter, WebSocketRoute, WebSocketRouter


@pytest.fixture
def http_router():
    return HTTPRouter()


@pytest.fixture
def ws_router():
    return WebSocketRouter()


async def mock_handler(request):
    return Response(content={"message": "test"})


def mock_middleware(handler):
    async def wrapped(request):
        request.middleware_called = True
        return await handler(request)
    return wrapped


def test_http_route_creation():
    route = HTTPRoute("/test", mock_handler, ["GET"])
    assert route.path == "/test"
    assert route.handler == mock_handler
    assert route.methods == ["GET"]
    assert route.name is None


def test_http_route_pattern_compilation():
    route = HTTPRoute("/users/{id}", mock_handler, ["GET"])
    assert route.pattern.pattern == r"^/users/(?P<id>[^/]+)$"


def test_http_route_match():
    route = HTTPRoute("/users/{id}", mock_handler, ["GET"])
    
    # Test matching path
    match = route.match("/users/123")
    assert match == {"id": "123"}
    
    # Test non-matching path
    match = route.match("/posts/123")
    assert match is None


def test_http_route_match_multiple_params():
    route = HTTPRoute("/users/{user_id}/posts/{post_id}", mock_handler, ["GET"])
    
    match = route.match("/users/123/posts/456")
    assert match == {"user_id": "123", "post_id": "456"}


@pytest.mark.asyncio
async def test_http_router_basic(http_router):
    http_router.add_route("/test", mock_handler, ["GET"])
    
    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [],
        "query_string": b"",
    })
    response = await http_router.handle_request(request)
    
    assert response.status_code == 200
    body = await response.body
    assert b"test" in body


@pytest.mark.asyncio
async def test_http_router_not_found(http_router):
    http_router.add_route("/test", mock_handler, ["GET"])
    
    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/nonexistent",
        "headers": [],
        "query_string": b"",
    })
    response = await http_router.handle_request(request)
    
    assert response.status_code == 404
    body = await response.body
    assert b"Not found" in body


def test_http_router_route_decorator(http_router):
    @http_router.route("/test", methods=["GET"])
    async def test_handler(request):
        return Response(content={"message": "test"})
    
    route = http_router.routes[0]
    assert route.path == "/test"
    assert route.methods == ["GET"]


@pytest.mark.asyncio
async def test_http_router_middleware(http_router):
    http_router.add_route("/test", mock_handler, ["GET"])
    http_router.add_middleware(mock_middleware)

    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [],
        "query_string": b"",
    })

    response = await http_router.handle_request(request)
    assert response.status_code == 200
    assert hasattr(request, "middleware_called")
    assert request.middleware_called is True


def test_http_router_middleware_decorator(http_router):
    @http_router.middleware()
    async def test_middleware(handler):
        async def wrapped(request):
            request.middleware_called = True
            return await handler(request)
        return wrapped
    
    assert len(http_router._middleware) == 1


def test_http_router_url_for(http_router):
    http_router.add_route("/users/{id}", mock_handler, ["GET"])
    http_router.routes[0].name = "user_detail"
    
    url = http_router.url_for("user_detail", id=123)
    assert url == "/users/123"


def test_http_router_url_for_not_found(http_router):
    with pytest.raises(ValueError):
        http_router.url_for("nonexistent")


def test_websocket_route_creation():
    route = WebSocketRoute("/ws", mock_handler)
    assert route.path == "/ws"
    assert route.handler == mock_handler
    assert route.name is None


def test_websocket_route_pattern_compilation():
    route = WebSocketRoute("/ws/{room}", mock_handler)
    # WebSocket pattern escapes forward slashes
    assert route.pattern.pattern == r"^\/ws\/(?P<room>[^/]+)$"


def test_websocket_route_match():
    route = WebSocketRoute("/ws/{room}", mock_handler)
    
    # Test matching path
    match = route.match("/ws/chat")
    assert match == {"room": "chat"}
    
    # Test non-matching path
    match = route.match("/api/ws")
    assert match is None


def test_websocket_router_add_route(ws_router):
    ws_router.add_route("/ws", mock_handler)
    assert len(ws_router.routes) == 1
    assert ws_router.routes[0].path == "/ws"


def test_websocket_router_decorator(ws_router):
    @ws_router.websocket("/ws")
    async def ws_handler(websocket):
        pass
    
    assert len(ws_router.routes) == 1
    assert ws_router.routes[0].path == "/ws"


def test_http_route_match_complex_path():
    route = HTTPRoute("/api/v1/users/{user_id}/posts/{post_id}/comments/{comment_id}", 
                     mock_handler, ["GET"])
    
    match = route.match("/api/v1/users/123/posts/456/comments/789")
    assert match == {
        "user_id": "123",
        "post_id": "456",
        "comment_id": "789"
    }


@pytest.mark.asyncio
async def test_http_router_method_not_allowed(http_router):
    http_router.add_route("/test", mock_handler, ["GET"])

    request = Request({
        "type": "http",
        "method": "POST",
        "path": "/test",
        "headers": [],
        "query_string": b"",
    })
    response = await http_router.handle_request(request)

    assert response.status_code == 405  # Method Not Allowed
    body = await response.body
    assert b"Method not allowed" in body


def test_http_route_match_empty_path():
    route = HTTPRoute("/", mock_handler, ["GET"])
    match = route.match("/")
    assert match == {}


@pytest.mark.asyncio
class TestHTTPRouter:
    async def test_route_matching(self, http_router):
        @http_router.route("/users/{user_id}")
        async def get_user(request):
            return Response(content={"user_id": request.path_params["user_id"]})

        request = Request({
            "type": "http",
            "method": "GET",
            "path": "/users/123",
            "headers": [],
            "query_string": b"",
        })

        response = await http_router.handle_request(request)
        assert response.status_code == 200
        body = await response.body
        assert b"123" in body

    async def test_route_not_found(self, http_router):
        request = Request({
            "type": "http",
            "method": "GET",
            "path": "/nonexistent",
            "headers": [],
            "query_string": b"",
        })

        response = await http_router.handle_request(request)
        assert response.status_code == 404

    async def test_route_methods(self, http_router):
        @http_router.route("/users", methods=["POST"])
        async def create_user(request):
            return Response(content={"status": "created"})

        # Test POST method
        request = Request({
            "type": "http",
            "method": "POST",
            "path": "/users",
            "headers": [],
            "query_string": b"",
        })
        response = await http_router.handle_request(request)
        assert response.status_code == 200

        # Test GET method (should fail)
        request = Request({
            "type": "http",
            "method": "GET",
            "path": "/users",
            "headers": [],
            "query_string": b"",
        })
        response = await http_router.handle_request(request)
        assert response.status_code == 405

    async def test_middleware(self, http_router):
        @http_router.middleware()
        def auth_middleware(handler):
            async def wrapper(request):
                request.middleware_called = True
                return await handler(request)
            return wrapper

        @http_router.route("/protected")
        async def protected_route(request):
            return Response(content={"status": "ok"})

        request = Request({
            "type": "http",
            "method": "GET",
            "path": "/protected",
            "headers": [],
            "query_string": b"",
        })

        response = await http_router.handle_request(request)
        assert response.status_code == 200
        assert hasattr(request, "middleware_called")
        assert request.middleware_called is True
