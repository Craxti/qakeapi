"""
Tests for Application class.
"""

import pytest

from qakeapi import JSONResponse, NotFound, QakeAPI, Request


@pytest.fixture
def app():
    """Create test application."""
    return QakeAPI(title="Test API", debug=True)


@pytest.mark.asyncio
async def test_app_creation(app):
    """Test application creation."""
    assert app.title == "Test API"
    assert app.debug is True
    assert len(app.router.routes) == 0


@pytest.mark.asyncio
async def test_app_route_registration(app):
    """Test route registration."""

    @app.get("/")
    async def root(request: Request):
        return {"message": "Hello"}

    assert len(app.router.routes) == 1
    route_match = app.router.find_route("/", "GET")
    assert route_match is not None


@pytest.mark.asyncio
async def test_app_route_handling():
    """Test route handling."""
    app = QakeAPI()

    @app.get("/test")
    async def test_handler(request: Request):
        return {"path": request.path}

    # Create mock ASGI scope
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "server": ("localhost", 8000),
    }

    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)

    # Check response was sent
    assert len(messages) == 2
    assert messages[0]["type"] == "http.response.start"
    assert messages[0]["status"] == 200


@pytest.mark.asyncio
async def test_app_not_found():
    """Test 404 handling."""
    app = QakeAPI()

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/nonexistent",
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "server": ("localhost", 8000),
    }

    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)

    # Should return 404
    assert len(messages) == 2
    assert messages[0]["type"] == "http.response.start"
    assert messages[0]["status"] == 404


@pytest.mark.asyncio
async def test_app_lifecycle_events(app):
    """Test lifecycle events."""
    startup_called = []
    shutdown_called = []

    @app.on_event("startup")
    async def startup():
        startup_called.append(True)

    @app.on_event("shutdown")
    async def shutdown():
        shutdown_called.append(True)

    # Trigger startup by making a request
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "server": ("localhost", 8000),
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        pass

    await app(scope, receive, send)

    assert len(startup_called) == 1
