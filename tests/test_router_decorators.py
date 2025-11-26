"""
Tests for router decorators.
"""

import pytest
from qakeapi.core.router import route, when


class TestRouteDecorator:
    """Tests for route decorator."""
    
    def test_route_decorator(self):
        """Test route decorator."""
        @route("/test", methods=["GET", "POST"])
        def handler():
            return {"test": True}
        
        assert hasattr(handler, "_route_path")
        assert handler._route_path == "/test"
        assert handler._route_methods == ["GET", "POST"]
    
    def test_route_decorator_default_method(self):
        """Test route decorator with default method."""
        @route("/test")
        def handler():
            return {"test": True}
        
        assert handler._route_methods == ["GET"]
    
    def test_route_decorator_with_condition(self):
        """Test route decorator with condition."""
        def condition(request):
            return True
        
        @route("/test", condition=condition)
        def handler():
            return {"test": True}
        
        assert handler._route_condition == condition
    
    def test_route_decorator_with_name(self):
        """Test route decorator with name."""
        @route("/test", name="test_route")
        def handler():
            return {"test": True}
        
        assert handler._route_name == "test_route"


class TestWhenDecorator:
    """Tests for when decorator."""
    
    def test_when_decorator(self):
        """Test when decorator."""
        def condition(request):
            return request.headers.get("X-Client") == "mobile"
        
        @when(condition)
        def handler(request):
            return {"mobile": True}
        
        assert handler._route_condition == condition
    
    def test_when_decorator_with_lambda(self):
        """Test when decorator with lambda."""
        @when(lambda req: req.path.startswith("/api"))
        def handler(request):
            return {"api": True}
        
        assert callable(handler._route_condition)

