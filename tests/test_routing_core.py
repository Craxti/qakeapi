import pytest
from qakeapi.core.routing import HTTPRoute, HTTPRouter, WebSocketRoute, WebSocketRouter, BaseRoute, BaseRouter


def test_base_route_creation():
    """Test base route creation"""
    class TestRoute(BaseRoute):
        def _compile_pattern(self, path):
            import re
            return re.compile(f"^{path}$")
        
        def match(self, path):
            match = self.pattern.match(path)
            return match.groupdict() if match else None
    
    route = TestRoute("/test", lambda x: x, "test_route")
    assert route.path == "/test"
    assert route.name == "test_route"


def test_base_router_creation():
    """Test base router creation"""
    class TestRouter(BaseRouter):
        def add_route(self, route):
            self.routes.append(route)
        
        async def handle_request(self, request):
            return {"status": "ok"}
    
    router = TestRouter()
    assert len(router.routes) == 0
    assert len(router._middleware) == 0


def test_http_route_methods():
    """Test HTTP route methods"""
    def handler(request):
        return {"message": "test"}
    
    route = HTTPRoute("/test", handler, ["GET", "POST"])
    assert "GET" in route.methods
    assert "POST" in route.methods
    assert len(route.methods) == 2


def test_http_route_pattern():
    """Test HTTP route pattern compilation"""
    route = HTTPRoute("/users/{id}/posts/{post_id}", lambda x: x, ["GET"])
    pattern = route.pattern.pattern
    assert "users" in pattern
    assert "posts" in pattern
    assert "id" in pattern
    assert "post_id" in pattern


def test_websocket_route_pattern():
    """Test WebSocket route pattern compilation"""
    route = WebSocketRoute("/ws/{room}", lambda x: x)
    pattern = route.pattern.pattern
    assert "ws" in pattern
    assert "room" in pattern


def test_route_matching():
    """Test route matching functionality"""
    route = HTTPRoute("/users/{user_id}/posts/{post_id}", lambda x: x, ["GET"])
    
    # Test successful match
    match = route.match("/users/123/posts/456")
    assert match is not None
    assert match["user_id"] == "123"
    assert match["post_id"] == "456"
    
    # Test failed match
    match = route.match("/users/123")
    assert match is None


def test_router_middleware():
    """Test router middleware functionality"""
    router = HTTPRouter()
    
    def test_middleware(handler):
        def wrapped(request):
            request.middleware_called = True
            return handler(request)
        return wrapped
    
    router.add_middleware(test_middleware)
    assert len(router._middleware) == 1


def test_router_url_generation():
    """Test URL generation for named routes"""
    router = HTTPRouter()
    router.add_route("/users/{id}/posts/{post_id}", lambda x: x, ["GET"], "user_post")
    
    url = router.url_for("user_post", id=123, post_id=456)
    assert url == "/users/123/posts/456"


def test_router_url_generation_missing_params():
    """Test URL generation with missing parameters"""
    router = HTTPRouter()
    router.add_route("/users/{id}/posts/{post_id}", lambda x: x, ["GET"], "user_post")
    
    # Missing parameters should remain as placeholders
    url = router.url_for("user_post", id=123)  # Missing post_id
    assert url == "/users/123/posts/{post_id}"


def test_router_duplicate_routes():
    """Test handling of duplicate routes"""
    router = HTTPRouter()
    
    def handler1(request):
        return {"message": "handler1"}
    
    def handler2(request):
        return {"message": "handler2"}
    
    # Add first route
    router.add_route("/test", handler1, ["GET"])
    assert len(router.routes) == 1
    
    # Add duplicate route - should update existing
    router.add_route("/test", handler2, ["GET"])
    assert len(router.routes) == 1
    assert router.routes[0].handler == handler2


def test_websocket_router_basic():
    """Test basic WebSocket router functionality"""
    router = WebSocketRouter()
    
    def ws_handler(websocket):
        pass
    
    router.add_route("/ws", ws_handler)
    assert len(router.routes) == 1
    assert router.routes[0].path == "/ws"
    assert router.routes[0].handler == ws_handler


def test_websocket_router_decorator():
    """Test WebSocket router decorator"""
    router = WebSocketRouter()
    
    @router.websocket("/ws")
    def ws_handler(websocket):
        pass
    
    assert len(router.routes) == 1
    assert router.routes[0].path == "/ws" 