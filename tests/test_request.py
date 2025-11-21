"""
Tests for Request class.
"""

import pytest
from qakeapi.core.request import Request


@pytest.fixture
def mock_scope():
    """Create mock ASGI scope."""
    return {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"param1=value1&param2=value2",
        "headers": [
            (b"content-type", b"application/json"),
            (b"host", b"localhost:8000"),
            (b"cookie", b"session=abc123; user=test"),
        ],
        "scheme": "http",
        "server": ("localhost", 8000),
        "client": ("127.0.0.1", 12345),
    }


@pytest.fixture
def mock_receive():
    """Create mock ASGI receive callable."""

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    return receive


@pytest.mark.asyncio
async def test_request_method(mock_scope, mock_receive):
    """Test request method property."""
    request = Request(mock_scope, mock_receive)
    assert request.method == "GET"


@pytest.mark.asyncio
async def test_request_path(mock_scope, mock_receive):
    """Test request path property."""
    request = Request(mock_scope, mock_receive)
    assert request.path == "/test"


@pytest.mark.asyncio
async def test_request_headers(mock_scope, mock_receive):
    """Test request headers."""
    request = Request(mock_scope, mock_receive)
    assert request.get_header("content-type") == "application/json"
    assert request.get_header("host") == "localhost:8000"


@pytest.mark.asyncio
async def test_request_query_params(mock_scope, mock_receive):
    """Test request query parameters."""
    request = Request(mock_scope, mock_receive)
    assert request.get_query_param("param1") == "value1"
    assert request.get_query_param("param2") == "value2"
    assert request.get_query_param("param3") is None


@pytest.mark.asyncio
async def test_request_cookies(mock_scope, mock_receive):
    """Test request cookies."""
    request = Request(mock_scope, mock_receive)
    assert request.get_cookie("session") == "abc123"
    assert request.get_cookie("user") == "test"
    assert request.get_cookie("nonexistent") is None


@pytest.mark.asyncio
async def test_request_path_params(mock_scope, mock_receive):
    """Test request path parameters."""
    request = Request(mock_scope, mock_receive, _path_params={"id": "123"})
    assert request.get_path_param("id") == "123"
    assert request.get_path_param("name") is None


@pytest.mark.asyncio
async def test_request_json(mock_scope, mock_receive):
    """Test request JSON parsing."""

    async def receive_json():
        return {
            "type": "http.request",
            "body": b'{"key": "value"}',
            "more_body": False,
        }

    request = Request(mock_scope, receive_json)
    data = await request.json()
    assert data == {"key": "value"}


@pytest.mark.asyncio
async def test_request_form(mock_scope, mock_receive):
    """Test request form parsing."""

    async def receive_form():
        return {
            "type": "http.request",
            "body": b"field1=value1&field2=value2",
            "more_body": False,
        }

    request = Request(mock_scope, receive_form)
    data = await request.form()
    assert data["field1"] == "value1"
    assert data["field2"] == "value2"
