"""
Integration tests for QakeAPI Application.
"""

import pytest
import json
from qakeapi import QakeAPI
from qakeapi.core.response import JSONResponse


class TestQakeAPIApp:
    """Tests for QakeAPI application."""
    
    @pytest.mark.asyncio
    async def test_simple_get_route(self, app, scope, receive, send):
        """Test simple GET route."""
        @app.get("/test")
        def handler():
            return {"message": "test"}
        
        scope["path"] = "/test"
        scope["method"] = "GET"
        
        await app(scope, receive, send)
        
        # Check response was sent
        assert len(send.messages) >= 1
        start_message = send.messages[0]
        assert start_message["type"] == "http.response.start"
        assert start_message["status"] == 200
    
    @pytest.mark.asyncio
    async def test_get_route_with_path_param(self, app, scope, receive, send):
        """Test GET route with path parameter."""
        @app.get("/users/{id}")
        def get_user(id: int):
            return {"id": id, "name": f"User {id}"}
        
        scope["path"] = "/users/123"
        scope["method"] = "GET"
        
        await app(scope, receive, send)
        
        # Check response was sent
        assert len(send.messages) >= 1
        start_message = send.messages[0]
        assert start_message["type"] == "http.response.start"
        assert start_message["status"] == 200
    
    @pytest.mark.asyncio
    async def test_post_route_with_body(self, app, scope, receive, send):
        """Test POST route with body."""
        class UserCreate:
            def __init__(self, name: str, email: str):
                self.name = name
                self.email = email
            
            def dict(self):
                return {"name": self.name, "email": self.email}
        
        @app.post("/users")
        async def create_user(user: UserCreate):
            return {"created": user.dict()}
        
        body_data = {"name": "John", "email": "john@example.com"}
        body_bytes = json.dumps(body_data).encode()
        
        scope["path"] = "/users"
        scope["method"] = "POST"
        scope["headers"] = [(b"content-type", b"application/json")]
        
        async def mock_receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}
        
        await app(scope, mock_receive, send)
        
        # Check response was sent
        assert len(send.messages) >= 1
    
    @pytest.mark.asyncio
    async def test_404_not_found(self, app, scope, receive, send):
        """Test 404 response for unknown route."""
        scope["path"] = "/unknown"
        scope["method"] = "GET"
        
        await app(scope, receive, send)
        
        # Check 404 response
        start_message = send.messages[0]
        assert start_message["type"] == "http.response.start"
        assert start_message["status"] == 404
    
    @pytest.mark.asyncio
    async def test_openapi_docs_endpoint(self, app, scope, receive, send):
        """Test /docs endpoint."""
        scope["path"] = "/docs"
        scope["method"] = "GET"
        
        await app(scope, receive, send)
        
        # Check HTML response
        assert len(send.messages) >= 1
        start_message = send.messages[0]
        assert start_message["type"] == "http.response.start"
        assert start_message["status"] == 200
    
    @pytest.mark.asyncio
    async def test_openapi_json_endpoint(self, app, scope, receive, send):
        """Test /openapi.json endpoint."""
        @app.get("/test")
        def handler():
            return {"message": "test"}
        
        scope["path"] = "/openapi.json"
        scope["method"] = "GET"
        
        await app(scope, receive, send)
        
        # Check JSON response
        assert len(send.messages) >= 1
        start_message = send.messages[0]
        assert start_message["type"] == "http.response.start"
        assert start_message["status"] == 200
    
    @pytest.mark.asyncio
    async def test_websocket_route(self, app, websocket_scope, websocket_receive, websocket_send):
        """Test WebSocket route."""
        from qakeapi import WebSocket
        
        @app.websocket("/ws/{room}")
        async def ws_handler(websocket: WebSocket, room: str):
            await websocket.accept()
            await websocket.send_json({"room": room})
        
        websocket_scope["path"] = "/ws/test-room"
        
        await app(websocket_scope, websocket_receive, websocket_send)
        
        # Check WebSocket accept
        accept_messages = [m for m in websocket_send.messages if m["type"] == "websocket.accept"]
        assert len(accept_messages) > 0
    
    @pytest.mark.asyncio
    async def test_middleware_integration(self, app, scope, receive, send):
        """Test middleware integration."""
        from qakeapi import CORSMiddleware
        
        app.add_middleware(CORSMiddleware(allow_origins=["*"]))
        
        @app.get("/test")
        def handler():
            return {"message": "test"}
        
        scope["path"] = "/test"
        scope["method"] = "GET"
        
        await app(scope, receive, send)
        
        # Check response was sent (middleware should not block)
        assert len(send.messages) >= 1
    
    @pytest.mark.asyncio
    async def test_startup_handler(self, app):
        """Test startup handler."""
        startup_called = []
        
        @app.on_startup
        def startup():
            startup_called.append(True)
        
        # Startup should be called on first request
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
        }
        
        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        
        async def send(message):
            pass
        
        @app.get("/test")
        def handler():
            return {"message": "test"}
        
        await app(scope, receive, send)
        
        # Startup should be called
        assert len(startup_called) == 1
    
    @pytest.mark.asyncio
    async def test_query_parameters(self, app, scope, receive, send):
        """Test query parameters."""
        @app.get("/search")
        def search(q: str, limit: int = 10):
            return {"query": q, "limit": limit}
        
        scope["path"] = "/search"
        scope["method"] = "GET"
        scope["query_string"] = b"q=test&limit=20"
        
        await app(scope, receive, send)
        
        # Response should be sent
        assert len(send.messages) >= 1

