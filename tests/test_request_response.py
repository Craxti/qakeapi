"""
Tests for Request and Response classes.
"""

import pytest
import json
from qakeapi.core.request import Request
from qakeapi.core.response import JSONResponse, HTMLResponse, TextResponse, Response


class TestRequest:
    """Tests for Request class."""
    
    @pytest.mark.asyncio
    async def test_request_creation(self, scope, receive):
        """Test request creation."""
        request = Request(scope, receive)
        assert request.method == "GET"
        assert request.path == "/test"
    
    @pytest.mark.asyncio
    async def test_request_query_params(self):
        """Test query parameters parsing."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "query_string": b"param1=value1&param2=value2",
        }
        
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        
        request = Request(scope, receive)
        assert "param1" in request.query_params
        assert request.query_params["param1"] == ["value1"]
        assert request.query_params["param2"] == ["value2"]
    
    @pytest.mark.asyncio
    async def test_request_headers(self):
        """Test headers parsing."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [(b"content-type", b"application/json"), (b"authorization", b"Bearer token123")],
        }
        
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        
        request = Request(scope, receive)
        assert request.headers.get("content-type") == "application/json"
        assert request.headers.get("authorization") == "Bearer token123"
    
    @pytest.mark.asyncio
    async def test_request_json(self):
        """Test JSON body parsing."""
        body_data = {"name": "John", "age": 30}
        body_bytes = json.dumps(body_data).encode()
        
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [(b"content-type", b"application/json")],
        }
        
        async def receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}
        
        request = Request(scope, receive)
        data = await request.json()
        assert data == body_data
        assert data["name"] == "John"
        assert data["age"] == 30
    
    @pytest.mark.asyncio
    async def test_request_json_empty(self):
        """Test empty JSON body."""
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [(b"content-type", b"application/json")],
        }
        
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        
        request = Request(scope, receive)
        # Empty body should return None or empty dict, not raise error
        result = await request.json()
        assert result in (None, {}, "")


class TestResponse:
    """Tests for Response classes."""
    
    def test_json_response(self):
        """Test JSONResponse creation."""
        data = {"message": "Hello", "status": "ok"}
        response = JSONResponse(data)
        
        assert response.status_code == 200
        assert response.media_type == "application/json"
        assert response._get_body() == json.dumps(data).encode()
    
    def test_json_response_with_status(self):
        """Test JSONResponse with custom status code."""
        data = {"error": "Not Found"}
        response = JSONResponse(data, status_code=404)
        
        assert response.status_code == 404
    
    def test_html_response(self):
        """Test HTMLResponse creation."""
        html_content = "<html><body>Hello</body></html>"
        response = HTMLResponse(html_content)
        
        assert response.status_code == 200
        assert response.media_type == "text/html"
        assert response._get_body() == html_content.encode()
    
    def test_text_response(self):
        """Test TextResponse creation."""
        text_content = "Hello, World!"
        response = TextResponse(text_content)
        
        assert response.status_code == 200
        assert response.media_type == "text/plain"
        assert response._get_body() == text_content.encode()
    
    def test_response_headers(self):
        """Test response headers."""
        response = JSONResponse({"message": "test"})
        response.headers["X-Custom-Header"] = "custom-value"
        
        headers = response._prepare_headers()
        headers_dict = {k.decode(): v.decode() for k, v in headers}
        
        assert "x-custom-header" in headers_dict or "X-Custom-Header" in headers_dict
        assert "content-type" in headers_dict

