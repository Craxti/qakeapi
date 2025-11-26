"""
Integration tests for QakeAPI app with rate limiting, caching, and DI.
"""

import pytest
from qakeapi import QakeAPI, Depends, rate_limit, cache
from qakeapi.core.response import JSONResponse


class TestAppIntegration:
    """Integration tests for QakeAPI app."""
    
    @pytest.mark.asyncio
    async def test_app_with_rate_limit(self, app, scope, receive, send):
        """Test app with rate limiting."""
        @rate_limit(requests_per_minute=10, window_seconds=60)
        @app.get("/rate-limited")
        def rate_limited_handler():
            return {"message": "rate limited"}
        
        scope["path"] = "/rate-limited"
        scope["method"] = "GET"
        
        await app(scope, receive, send)
        
        # Should succeed
        start_msg = [m for m in send.messages if m.get("type") == "http.response.start"]
        assert start_msg[0]["status"] == 200
    
    @pytest.mark.asyncio
    async def test_app_with_cache(self, app, scope, receive, send):
        """Test app with caching."""
        call_count = [0]
        
        @cache(ttl=60)
        @app.get("/cached")
        def cached_handler():
            call_count[0] += 1
            return {"count": call_count[0]}
        
        scope["path"] = "/cached"
        scope["method"] = "GET"
        
        # First call
        messages1 = []
        async def send1(msg):
            messages1.append(msg)
        
        await app(scope, receive, send1)
        
        # Second call - should use cache
        messages2 = []
        async def send2(msg):
            messages2.append(msg)
        
        await app(scope, receive, send2)
        
        # Both should succeed
        start1 = [m for m in messages1 if m.get("type") == "http.response.start"]
        start2 = [m for m in messages2 if m.get("type") == "http.response.start"]
        assert start1[0]["status"] == 200
        assert start2[0]["status"] == 200
    
    @pytest.mark.asyncio
    async def test_app_with_dependency_injection(self, app, scope, receive, send):
        """Test app with dependency injection."""
        def get_database(request=None):
            return {"type": "database", "connected": True}
        
        @app.get("/with-di")
        async def handler_with_di(db=Depends(get_database)):
            return {"db": db}
        
        scope["path"] = "/with-di"
        scope["method"] = "GET"
        
        await app(scope, receive, send)
        
        start_msg = [m for m in send.messages if m.get("type") == "http.response.start"]
        assert start_msg[0]["status"] == 200
    
    @pytest.mark.asyncio
    async def test_app_with_cached_dependency(self, app, scope, receive, send):
        """Test app with cached dependency."""
        call_count = [0]
        
        def get_config(request=None):
            call_count[0] += 1
            return {"config": "value", "calls": call_count[0]}
        
        @app.get("/with-cached-di")
        async def handler_with_cached_di(config=Depends(get_config, cache=True)):
            return {"config": config}
        
        scope["path"] = "/with-cached-di"
        scope["method"] = "GET"
        
        # First call
        messages1 = []
        async def send1(msg):
            messages1.append(msg)
        
        await app(scope, receive, send1)
        
        # Second call - dependency should be cached
        messages2 = []
        async def send2(msg):
            messages2.append(msg)
        
        await app(scope, receive, send2)
        
        # Both should succeed
        start1 = [m for m in messages1 if m.get("type") == "http.response.start"]
        start2 = [m for m in messages2 if m.get("type") == "http.response.start"]
        assert start1[0]["status"] == 200
        assert start2[0]["status"] == 200
    
    @pytest.mark.asyncio
    async def test_app_with_rate_limit_and_cache(self, app, scope, receive, send):
        """Test app with both rate limiting and caching."""
        @rate_limit(requests_per_minute=5)
        @cache(ttl=60)
        @app.get("/combined")
        def combined_handler():
            return {"message": "combined"}
        
        scope["path"] = "/combined"
        scope["method"] = "GET"
        
        await app(scope, receive, send)
        
        start_msg = [m for m in send.messages if m.get("type") == "http.response.start"]
        assert start_msg[0]["status"] == 200
    
    @pytest.mark.asyncio
    async def test_app_error_handling_with_exceptions(self, app, scope, receive, send):
        """Test app error handling with HTTP exceptions."""
        from qakeapi.core.exceptions import NotFoundError, ValidationError
        
        @app.get("/not-found")
        def not_found_handler():
            raise NotFoundError("Resource not found")
        
        scope["path"] = "/not-found"
        scope["method"] = "GET"
        
        await app(scope, receive, send)
        
        start_msg = [m for m in send.messages if m.get("type") == "http.response.start"]
        assert start_msg[0]["status"] == 404
        
        @app.post("/validation-error")
        async def validation_error_handler(request):
            raise ValidationError("Validation failed", errors={"field": ["Required"]})
        
        scope["path"] = "/validation-error"
        scope["method"] = "POST"
        
        messages2 = []
        async def send2(msg):
            messages2.append(msg)
        
        await app(scope, receive, send2)
        
        start_msg2 = [m for m in messages2 if m.get("type") == "http.response.start"]
        assert start_msg2[0]["status"] == 400

