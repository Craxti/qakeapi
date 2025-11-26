"""
Extended tests for Request class to increase coverage.
"""

import pytest
from qakeapi.core.request import Request


class TestRequestExtended:
    """Extended tests for Request."""
    
    @pytest.mark.asyncio
    async def test_request_form_data(self):
        """Test form data parsing."""
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [(b"content-type", b"application/x-www-form-urlencoded")],
        }
        
        body = b"name=John&age=30"
        
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        
        request = Request(scope, receive)
        form_data = await request.form()
        
        assert "name" in form_data
        assert form_data["name"] == "John"
        assert form_data["age"] == "30"
    
    @pytest.mark.asyncio
    async def test_request_body_chunks(self):
        """Test request body with chunks."""
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [(b"content-type", b"application/json")],
        }
        
        chunks = [b'{"name":', b' "John"}']
        chunk_index = [0]
        
        async def receive():
            if chunk_index[0] < len(chunks):
                result = {
                    "type": "http.request",
                    "body": chunks[chunk_index[0]],
                    "more_body": chunk_index[0] < len(chunks) - 1,
                }
                chunk_index[0] += 1
                return result
            return {"type": "http.request", "body": b"", "more_body": False}
        
        request = Request(scope, receive)
        body = await request.body()
        
        assert b"John" in body
    
    @pytest.mark.asyncio
    async def test_request_client(self):
        """Test request client info."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "client": ("127.0.0.1", 12345),
        }
        
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        
        request = Request(scope, receive)
        assert request.client is not None
    
    @pytest.mark.asyncio
    async def test_request_server(self):
        """Test request server info."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "server": ("localhost", 8000),
        }
        
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        
        request = Request(scope, receive)
        # Check server is in scope
        assert request.scope.get("server") == ("localhost", 8000)

