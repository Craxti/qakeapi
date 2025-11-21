"""
Tests for Router classes.
"""

import pytest
from qakeapi.core.router import Router, APIRouter, Route


def test_route_creation():
    """Test route creation."""
    def handler(request):
        return {"message": "test"}
    
    route = Route("/test", handler, ["GET"])
    assert route.path == "/test"
    assert "GET" in route.methods
    assert route.handler == handler


def test_route_pattern_matching():
    """Test route pattern matching."""
    def handler(request):
        return {"message": "test"}
    
    route = Route("/users/{user_id}", handler, ["GET"])
    params = route.match("/users/123")
    assert params is not None
    assert params["user_id"] == "123"
    
    # Should not match different path
    assert route.match("/posts/123") is None


def test_router_add_route():
    """Test router route addition."""
    router = Router()
    
    def handler(request):
        return {"message": "test"}
    
    router.add_route("/test", handler, ["GET"])
    assert len(router.routes) == 1


def test_router_find_route():
    """Test router route finding."""
    router = Router()
    
    def handler(request):
        return {"message": "test"}
    
    router.add_route("/test", handler, ["GET"])
    route_match = router.find_route("/test", "GET")
    
    assert route_match is not None
    route, params = route_match
    assert route.path == "/test"
    assert params == {}


def test_router_find_route_with_params():
    """Test router route finding with parameters."""
    router = Router()
    
    def handler(request):
        return {"message": "test"}
    
    router.add_route("/users/{user_id}", handler, ["GET"])
    route_match = router.find_route("/users/123", "GET")
    
    assert route_match is not None
    route, params = route_match
    assert params["user_id"] == "123"


def test_router_decorators():
    """Test router decorators."""
    router = Router()
    
    @router.get("/test")
    def get_handler(request):
        return {"method": "GET"}
    
    @router.post("/test")
    def post_handler(request):
        return {"method": "POST"}
    
    assert len(router.routes) == 2
    
    # Check GET route
    route_match = router.find_route("/test", "GET")
    assert route_match is not None
    
    # Check POST route
    route_match = router.find_route("/test", "POST")
    assert route_match is not None


def test_api_router_prefix():
    """Test APIRouter prefix."""
    router = APIRouter(prefix="/api/v1")
    
    def handler(request):
        return {"message": "test"}
    
    router.add_route("/users", handler, ["GET"])
    
    # Route should have prefix
    assert len(router.routes) == 1
    assert router.routes[0].path == "/api/v1/users"

