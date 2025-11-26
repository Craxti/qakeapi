"""
Extended tests for Response classes to increase coverage.
"""

import pytest
from qakeapi.core.response import Response, JSONResponse, HTMLResponse, TextResponse


class TestResponseExtended:
    """Extended tests for Response."""
    
    @pytest.mark.asyncio
    async def test_response_asgi_interface(self):
        """Test Response ASGI interface."""
        response = JSONResponse({"message": "test"})
        
        messages = []
        
        async def send(message):
            messages.append(message)
        
        await response(send)
        
        assert len(messages) == 2
        assert messages[0]["type"] == "http.response.start"
        assert messages[1]["type"] == "http.response.body"
    
    def test_response_custom_status(self):
        """Test response with custom status code."""
        response = JSONResponse({"error": "Not Found"}, status_code=404)
        assert response.status_code == 404
    
    def test_response_custom_headers(self):
        """Test response with custom headers."""
        response = JSONResponse({"message": "test"})
        response.headers["X-Custom"] = "value"
        
        headers = response._prepare_headers()
        headers_dict = {k.decode(): v.decode() for k, v in headers}
        
        assert "x-custom" in headers_dict or "X-Custom" in headers_dict
    
    def test_html_response_encoding(self):
        """Test HTML response encoding."""
        html = "<html><body>Test</body></html>"
        response = HTMLResponse(html)
        
        body = response._get_body()
        assert isinstance(body, bytes)
    
    def test_text_response_encoding(self):
        """Test text response encoding."""
        text = "Hello, World! Test"
        response = TextResponse(text)
        
        body = response._get_body()
        assert isinstance(body, bytes)


