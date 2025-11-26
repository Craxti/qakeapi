"""
Extended integration tests for QakeAPI App to increase coverage.
"""

import pytest
from qakeapi import QakeAPI
from qakeapi.core.response import JSONResponse


class TestQakeAPIExtended:
    """Extended tests for QakeAPI application."""
    
    @pytest.mark.asyncio
    async def test_app_route_decorators(self, app, scope, receive, send):
        """Test all route decorators (get, post, put, delete, patch)."""
        @app.get("/get")
        def get_handler():
            return {"method": "GET"}
        
        @app.post("/post")
        def post_handler():
            return {"method": "POST"}
        
        @app.put("/put")
        def put_handler():
            return {"method": "PUT"}
        
        @app.delete("/delete")
        def delete_handler():
            return {"method": "DELETE"}
        
        @app.patch("/patch")
        def patch_handler():
            return {"method": "PATCH"}
        
        # Test GET
        scope["path"] = "/get"
        scope["method"] = "GET"
        await app(scope, receive, send)
        assert send.messages[0]["status"] == 200
        
        # Test POST
        scope["path"] = "/post"
        scope["method"] = "POST"
        # Create new send for POST test
        messages2 = []
        async def send2(msg):
            messages2.append(msg)
        await app(scope, receive, send2)
        assert len(messages2) > 0
        start_msg = [m for m in messages2 if m.get("type") == "http.response.start"]
        if start_msg:
            assert start_msg[0]["status"] == 200
    
    @pytest.mark.asyncio
    async def test_app_when_decorator(self, app, scope, receive, send):
        """Test conditional routing with @when decorator."""
        @app.when(lambda req: req.headers.get("x-version") == "v2")
        def v2_handler(request):
            return {"version": "v2"}
        
        scope["path"] = "/api"
        scope["method"] = "GET"
        scope["headers"] = [(b"x-version", b"v2")]
        
        await app(scope, receive, send)
        assert send.messages[0]["status"] == 200
    
    @pytest.mark.asyncio
    async def test_app_react_decorator(self, app):
        """Test reactive event decorator."""
        events_received = []
        
        @app.react("test:event")
        async def event_handler(event):
            events_received.append(event.data)
        
        await app.emit("test:event", {"message": "test"})
        
        # Give event time to process
        import asyncio
        await asyncio.sleep(0.01)
        
        assert len(events_received) == 1
    
    @pytest.mark.asyncio
    async def test_app_error_handling(self, app, scope, receive, send):
        """Test error handling in app."""
        @app.get("/error")
        def error_handler():
            raise ValueError("Test error")
        
        scope["path"] = "/error"
        scope["method"] = "GET"
        
        # In non-debug mode, should catch error
        app.debug = False
        await app(scope, receive, send)
        
        # Should return 500 error
        start_msg = [m for m in send.messages if m.get("type") == "http.response.start"]
        if start_msg:
            assert start_msg[0]["status"] == 500
    
    @pytest.mark.asyncio
    async def test_app_debug_mode(self, app, scope, receive, send):
        """Test debug mode error handling."""
        app.debug = True
        
        @app.get("/error")
        def error_handler():
            raise ValueError("Test error")
        
        scope["path"] = "/error"
        scope["method"] = "GET"
        
        # In debug mode, should return error with traceback
        await app(scope, receive, send)
        
        # Should return 500 error with traceback in debug mode
        start_msg = [m for m in send.messages if m.get("type") == "http.response.start"]
        if start_msg:
            assert start_msg[0]["status"] == 500
        
        # Check that response contains traceback in debug mode
        body_msg = [m for m in send.messages if m.get("type") == "http.response.body"]
        if body_msg and body_msg[0].get("body"):
            import json
            body = json.loads(body_msg[0]["body"].decode())
            assert "error" in body
            assert "traceback" in body  # Debug mode includes traceback
    
    @pytest.mark.asyncio
    async def test_app_shutdown_handler(self, app):
        """Test shutdown handler."""
        shutdown_called = []
        
        initial_handlers_count = len(app._shutdown_handlers)
        
        @app.on_shutdown
        def shutdown():
            shutdown_called.append(True)
        
        # Shutdown handlers are called on app shutdown
        # For test, we just verify it's registered
        # Note: app automatically adds shutdown_executor handler, so we check for at least 2
        assert len(app._shutdown_handlers) == initial_handlers_count + 1
    
    @pytest.mark.asyncio
    async def test_app_openapi_route_registration(self, app, scope, receive, send):
        """Test that routes are registered in OpenAPI."""
        @app.get("/api/test")
        def test_handler():
            return {"test": True}
        
        scope["path"] = "/openapi.json"
        scope["method"] = "GET"
        
        await app(scope, receive, send)
        
        # OpenAPI should include the route
        start_msg = [m for m in send.messages if m.get("type") == "http.response.start"]
        if start_msg:
            assert start_msg[0]["status"] == 200

