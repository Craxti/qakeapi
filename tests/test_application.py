import pytest
import asyncio
from qakeapi.core.application import Application
from qakeapi.core.responses import Response
from qakeapi.core.routing import HTTPRouter, WebSocketRouter
from qakeapi.core.cache import Cache


@pytest.mark.asyncio
class TestApplication:
    async def test_http_request(self):
        app = Application()

        # Add test route
        @app.route("/")
        async def test_handler(request):
            return Response({"message": "Hello, World!"}, status_code=200)

        # Create test scope
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
        }

        # Create test receive and send functions
        received_messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            received_messages.append(message)

        # Call application
        await app(scope, receive, send)

        # Check response
        assert len(received_messages) == 2
        assert received_messages[0]["type"] == "http.response.start"
        assert received_messages[0]["status"] == 200
        assert received_messages[1]["type"] == "http.response.body"
        assert received_messages[1]["body"] == b'{"message": "Hello, World!"}'

    async def test_websocket_request(self):
        app = Application()

        # Create test scope
        scope = {
            "type": "websocket",
            "path": "/ws",
            "headers": [],
        }

        # Create test receive and send functions
        received_messages = []

        async def receive():
            return {"type": "websocket.connect"}

        async def send(message):
            received_messages.append(message)

        # Call application
        await app(scope, receive, send)

        # Check response
        assert len(received_messages) == 1
        assert received_messages[0]["type"] == "websocket.close"

    async def test_lifespan_events(self):
        app = Application()

        # Create test scope
        scope = {
            "type": "lifespan",
        }

        # Create test receive and send functions
        received_messages = []
        startup_complete = False
        shutdown_complete = False

        async def receive():
            nonlocal startup_complete, shutdown_complete
            if not startup_complete:
                startup_complete = True
                return {"type": "lifespan.startup"}
            if not shutdown_complete:
                shutdown_complete = True
                return {"type": "lifespan.shutdown"}
            return {"type": "lifespan.shutdown"}  # Should never reach here

        async def send(message):
            received_messages.append(message)

        # Call application
        await app(scope, receive, send)

        # Check responses
        assert len(received_messages) == 2
        assert received_messages[0]["type"] == "lifespan.startup.complete"
        assert received_messages[1]["type"] == "lifespan.shutdown.complete"

    def test_route_decorators(self):
        app = Application()
        
        @app.get("/test")
        async def test_get(request):
            return {"method": "GET"}
        
        @app.post("/test")
        async def test_post(request):
            return {"method": "POST"}
        
        # Check that routes are added
        assert len(app.http_router.routes) == 3  # 2 + /docs and /openapi.json


@pytest.mark.asyncio
async def test_memory_cache_set_get():
    cache = Cache(backend="memory")
    await cache.set("foo", "bar")
    value = await cache.get("foo")
    assert value == "bar"

@pytest.mark.asyncio
async def test_memory_cache_delete():
    cache = Cache(backend="memory")
    await cache.set("foo", "bar")
    await cache.delete("foo")
    value = await cache.get("foo")
    assert value is None

@pytest.mark.asyncio
async def test_memory_cache_clear():
    cache = Cache(backend="memory")
    await cache.set("foo", "bar")
    await cache.set("baz", 123)
    await cache.clear()
    assert await cache.get("foo") is None
    assert await cache.get("baz") is None

@pytest.mark.asyncio
async def test_memory_cache_ttl():
    cache = Cache(backend="memory")
    await cache.set("foo", "bar", ttl=1)
    value = await cache.get("foo")
    assert value == "bar"
    await asyncio.sleep(1.1)
    value = await cache.get("foo")
    assert value is None
