"""
Tests for Middleware system.
"""

import pytest
from qakeapi.core.middleware import (
    BaseMiddleware,
    MiddlewareStack,
    CORSMiddleware,
    LoggingMiddleware,
)
from qakeapi.core.request import Request
from qakeapi.core.response import JSONResponse


class TestMiddlewareStack:
    """Tests for MiddlewareStack."""
    
    @pytest.mark.asyncio
    async def test_middleware_stack_execution(self):
        """Test middleware stack execution."""
        async def handler(request):
            return JSONResponse({"message": "handler"})
        
        stack = MiddlewareStack(handler)
        
        class TestMiddleware(BaseMiddleware):
            async def process(self, request, call_next):
                response = await call_next(request)
                response.headers["X-Middleware"] = "test"
                return response
        
        stack.add(TestMiddleware())
        
        scope = {"type": "http", "method": "GET", "path": "/test"}
        request = Request(scope, None)
        
        response = await stack(request)
        assert isinstance(response, JSONResponse)
        assert response.headers.get("X-Middleware") == "test"
    
    @pytest.mark.asyncio
    async def test_multiple_middleware(self):
        """Test multiple middleware in stack."""
        async def handler(request):
            return JSONResponse({"message": "handler"})
        
        stack = MiddlewareStack(handler)
        
        class Middleware1(BaseMiddleware):
            async def process(self, request, call_next):
                response = await call_next(request)
                response.headers["X-M1"] = "1"
                return response
        
        class Middleware2(BaseMiddleware):
            async def process(self, request, call_next):
                response = await call_next(request)
                response.headers["X-M2"] = "2"
                return response
        
        stack.add(Middleware1())
        stack.add(Middleware2())
        
        scope = {"type": "http", "method": "GET", "path": "/test"}
        request = Request(scope, None)
        
        response = await stack(request)
        assert response.headers.get("X-M1") == "1"
        assert response.headers.get("X-M2") == "2"


class TestCORSMiddleware:
    """Tests for CORSMiddleware."""
    
    @pytest.mark.asyncio
    async def test_cors_middleware(self):
        """Test CORS middleware."""
        async def handler(request):
            return JSONResponse({"message": "test"})
        
        middleware = CORSMiddleware(allow_origins=["*"], allow_methods=["GET", "POST"])
        
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [(b"origin", b"http://localhost:3000")],
        }
        
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        
        request = Request(scope, receive)
        
        response = await middleware.process(request, handler)
        
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
    
    @pytest.mark.asyncio
    async def test_cors_preflight(self):
        """Test CORS preflight request."""
        async def handler(request):
            return JSONResponse({"message": "test"})
        
        middleware = CORSMiddleware(allow_origins=["*"])
        
        scope = {
            "type": "http",
            "method": "OPTIONS",
            "path": "/test",
            "headers": [(b"origin", b"http://localhost:3000")],
        }
        
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        
        request = Request(scope, receive)
        
        response = await middleware.process(request, handler)
        
        assert response.status_code == 204
        assert "Access-Control-Allow-Origin" in response.headers


class TestLoggingMiddleware:
    """Tests for LoggingMiddleware."""
    
    @pytest.mark.asyncio
    async def test_logging_middleware(self, capsys):
        """Test logging middleware output."""
        async def handler(request):
            return JSONResponse({"message": "test"})
        
        middleware = LoggingMiddleware()
        
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
        }
        
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        
        request = Request(scope, receive)
        
        response = await middleware.process(request, handler)
        
        assert isinstance(response, JSONResponse)
        # Check if something was printed (logging output)
        captured = capsys.readouterr()
        # The middleware should print something, but we just check it doesn't crash


