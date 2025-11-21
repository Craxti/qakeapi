"""
Tests for Response classes.
"""

import pytest
from qakeapi.core.response import (
    Response,
    JSONResponse,
    HTMLResponse,
    TextResponse,
    RedirectResponse,
    FileResponse,
)


def test_response_basic():
    """Test basic Response."""
    response = Response(content="test", status_code=200)
    assert response.status_code == 200
    assert response.content == "test"
    assert response.render() == b"test"


def test_json_response():
    """Test JSONResponse."""
    response = JSONResponse({"message": "hello"})
    assert response.status_code == 200
    assert response.media_type == "application/json"
    assert b"message" in response.render()
    assert b"hello" in response.render()


def test_html_response():
    """Test HTMLResponse."""
    response = HTMLResponse("<html><body>Test</body></html>")
    assert response.status_code == 200
    assert response.media_type == "text/html; charset=utf-8"
    assert b"<html>" in response.render()


def test_text_response():
    """Test TextResponse."""
    response = TextResponse("Hello, World!")
    assert response.status_code == 200
    assert response.media_type == "text/plain; charset=utf-8"
    assert response.render() == b"Hello, World!"


def test_redirect_response():
    """Test RedirectResponse."""
    response = RedirectResponse("/new-path", status_code=302)
    assert response.status_code == 302
    assert response.headers["location"] == "/new-path"


def test_response_cookies():
    """Test response cookie setting."""
    response = Response()
    response.set_cookie("session", "abc123", max_age=3600)
    assert "session" in response.cookies
    assert "set-cookie" in response.headers


def test_response_delete_cookie():
    """Test response cookie deletion."""
    response = Response()
    response.set_cookie("session", "abc123")
    response.delete_cookie("session")
    assert "session" in response.cookies
    # Cookie should have max_age=0
    assert "Max-Age=0" in response.cookies["session"]
