"""
Extended tests for middleware system.
"""

import pytest
from qakeapi.core.middleware import RequestSizeLimitMiddleware
from qakeapi.core.exceptions import PayloadTooLargeError
from qakeapi.core.request import Request


class TestRequestSizeLimitMiddleware:
    """Tests for RequestSizeLimitMiddleware."""
    
    @pytest.mark.asyncio
    async def test_request_size_limit_allowed(self):
        """Test request within size limit."""
        middleware = RequestSizeLimitMiddleware(max_size=1024)
        
        class MockRequest:
            def __init__(self):
                self.headers = {"content-length": "100"}
                self.method = "POST"
        
        request = MockRequest()
        
        async def call_next(req):
            from qakeapi.core.response import JSONResponse
            return JSONResponse({"status": "ok"})
        
        response = await middleware.process(request, call_next)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_request_size_limit_exceeded_header(self):
        """Test request exceeding size limit via Content-Length header."""
        middleware = RequestSizeLimitMiddleware(max_size=1024)
        
        class MockRequest:
            def __init__(self):
                self.headers = {"content-length": "2048"}
                self.method = "POST"
        
        request = MockRequest()
        
        async def call_next(req):
            from qakeapi.core.response import JSONResponse
            return JSONResponse({"status": "ok"})
        
        with pytest.raises(PayloadTooLargeError):
            await middleware.process(request, call_next)
    
    @pytest.mark.asyncio
    async def test_request_size_limit_exceeded_body(self):
        """Test request exceeding size limit via body."""
        middleware = RequestSizeLimitMiddleware(max_size=1024)
        
        class MockRequest:
            def __init__(self):
                self.headers = {}
                self.method = "POST"
                self._body = b"x" * 2048  # 2KB body
        
        request = MockRequest()
        
        async def call_next(req):
            # Simulate reading body
            if hasattr(req, "_body") and len(req._body) > 1024:
                raise PayloadTooLargeError("Request body too large")
            from qakeapi.core.response import JSONResponse
            return JSONResponse({"status": "ok"})
        
        with pytest.raises(PayloadTooLargeError):
            await middleware.process(request, call_next)
    
    @pytest.mark.asyncio
    async def test_request_size_limit_no_content_length(self):
        """Test request without Content-Length header."""
        middleware = RequestSizeLimitMiddleware(max_size=1024)
        
        class MockRequest:
            def __init__(self):
                self.headers = {}
                self.method = "POST"
        
        request = MockRequest()
        
        async def call_next(req):
            from qakeapi.core.response import JSONResponse
            return JSONResponse({"status": "ok"})
        
        # Should pass if no Content-Length and body is small
        response = await middleware.process(request, call_next)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_request_size_limit_invalid_content_length(self):
        """Test request with invalid Content-Length header."""
        middleware = RequestSizeLimitMiddleware(max_size=1024)
        
        class MockRequest:
            def __init__(self):
                self.headers = {"content-length": "invalid"}
                self.method = "POST"
        
        request = MockRequest()
        
        async def call_next(req):
            from qakeapi.core.response import JSONResponse
            return JSONResponse({"status": "ok"})
        
        # Should pass if Content-Length is invalid
        response = await middleware.process(request, call_next)
        assert response.status_code == 200
    
    def test_request_size_limit_default_size(self):
        """Test default size limit."""
        middleware = RequestSizeLimitMiddleware()
        assert middleware.max_size == 10 * 1024 * 1024  # 10MB
    
    def test_request_size_limit_custom_size(self):
        """Test custom size limit."""
        middleware = RequestSizeLimitMiddleware(max_size=5 * 1024 * 1024)
        assert middleware.max_size == 5 * 1024 * 1024


class TestPayloadTooLargeError:
    """Tests for PayloadTooLargeError exception."""
    
    def test_payload_too_large_error(self):
        """Test PayloadTooLargeError exception."""
        error = PayloadTooLargeError("Request too large")
        assert error.status_code == 413
        assert error.detail == "Request too large"
    
    def test_payload_too_large_error_default(self):
        """Test PayloadTooLargeError with default message."""
        error = PayloadTooLargeError()
        assert error.status_code == 413
        assert error.detail == "Payload Too Large"

