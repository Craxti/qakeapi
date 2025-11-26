"""
Tests for Router and Route matching.
"""

import pytest
from qakeapi.core.router import Router, Route
from qakeapi.core.request import Request


class TestRouter:
    """Tests for Router."""
    
    def test_add_route(self):
        """Test adding a route."""
        router = Router()
        
        def handler():
            return "test"
        
        router.add_route("/test", handler, methods=["GET"])
        assert len(router.routes) == 1
    
    def test_find_route_exact_match(self):
        """Test finding exact route match."""
        router = Router()
        
        def handler():
            return "test"
        
        router.add_route("/test", handler, methods=["GET"])
        
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
        }
        request = Request(scope, None)
        
        route_match = router.find_route("/test", "GET", request)
        assert route_match is not None
        route, params = route_match
        assert route.handler == handler
        assert params == {}
    
    def test_find_route_with_params(self):
        """Test finding route with path parameters."""
        router = Router()
        
        def handler(id: int):
            return f"user_{id}"
        
        router.add_route("/users/{id}", handler, methods=["GET"])
        
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/users/123",
        }
        request = Request(scope, None)
        
        route_match = router.find_route("/users/123", "GET", request)
        assert route_match is not None
        route, params = route_match
        assert route.handler == handler
        assert params == {"id": "123"}
    
    def test_find_route_not_found(self):
        """Test route not found."""
        router = Router()
        
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/unknown",
        }
        request = Request(scope, None)
        
        route_match = router.find_route("/unknown", "GET", request)
        assert route_match is None
    
    def test_find_route_wrong_method(self):
        """Test route with wrong HTTP method."""
        router = Router()
        
        def handler():
            return "test"
        
        router.add_route("/test", handler, methods=["GET"])
        
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/test",
        }
        request = Request(scope, None)
        
        route_match = router.find_route("/test", "POST", request)
        assert route_match is None
    
    def test_multiple_routes(self):
        """Test multiple routes."""
        router = Router()
        
        def handler1():
            return "handler1"
        
        def handler2():
            return "handler2"
        
        router.add_route("/route1", handler1, methods=["GET"])
        router.add_route("/route2", handler2, methods=["GET"])
        
        assert len(router.routes) == 2
        
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/route1",
        }
        request = Request(scope, None)
        
        route_match = router.find_route("/route1", "GET", request)
        assert route_match is not None
        route, _ = route_match
        assert route.handler == handler1
    
    def test_route_with_condition(self):
        """Test route with condition."""
        router = Router()
        
        def handler():
            return "conditioned"
        
        def condition(request):
            return request.headers.get("x-special") == "true"
        
        router.add_route("/test", handler, methods=["GET"], condition=condition)
        
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [(b"x-special", b"true")],
        }
        request = Request(scope, None)
        
        route_match = router.find_route("/test", "GET", request)
        assert route_match is not None
        
        # Test with condition not met
        scope2 = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
        }
        request2 = Request(scope2, None)
        
        route_match2 = router.find_route("/test", "GET", request2)
        assert route_match2 is None


class TestRoute:
    """Tests for Route class."""
    
    def test_route_creation(self):
        """Test route creation."""
        def handler():
            return "test"
        
        route = Route("/test", handler, methods=["GET"])
        assert route.path == "/test"
        assert route.handler == handler
        assert "GET" in route.methods
    
    def test_route_match_simple(self):
        """Test simple route matching."""
        def handler():
            return "test"
        
        route = Route("/test", handler, methods=["GET"])
        scope = {"type": "http", "method": "GET", "path": "/test"}
        request = Request(scope, None)
        params = route.match("/test", "GET", request)
        assert params == {}
        
        params2 = route.match("/other", "GET", request)
        assert params2 is None
    
    def test_route_match_with_params(self):
        """Test route matching with parameters."""
        def handler(id: int):
            return f"user_{id}"
        
        route = Route("/users/{id}", handler, methods=["GET"])
        scope = {"type": "http", "method": "GET", "path": "/users/123"}
        request = Request(scope, None)
        params = route.match("/users/123", "GET", request)
        assert params == {"id": "123"}
        
        params2 = route.match("/users/456", "GET", request)
        assert params2 == {"id": "456"}

