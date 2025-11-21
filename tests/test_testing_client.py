"""
Tests for test client.
"""

import pytest

from qakeapi import QakeAPI, Request
from qakeapi.testing import TestClient, TestResponse


@pytest.fixture
def app():
    """Create test application."""
    app = QakeAPI()

    @app.get("/")
    async def root():
        return {"message": "Hello"}

    @app.get("/users/{user_id}")
    async def get_user(user_id: int):
        return {"user_id": user_id}

    @app.post("/users")
    async def create_user(request: Request):
        data = await request.json()
        return {"created": data}

    return app


def test_test_client_get(app):
    """Test TestClient GET request."""
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}


def test_test_client_path_params(app):
    """Test TestClient with path parameters."""
    client = TestClient(app)
    response = client.get("/users/123")

    assert response.status_code == 200
    # Path params are converted to int by router
    assert response.json()["user_id"] == 123 or response.json()["user_id"] == "123"


def test_test_client_post(app):
    """Test TestClient POST request."""
    client = TestClient(app)
    response = client.post("/users", json={"name": "John", "age": 30})

    assert response.status_code == 200
    assert "created" in response.json()


def test_test_response_json(app):
    """Test TestResponse JSON parsing."""
    client = TestClient(app)
    response = client.get("/")

    data = response.json()
    assert isinstance(data, dict)
    assert data["message"] == "Hello"


def test_test_response_text(app):
    """Test TestResponse text property."""
    client = TestClient(app)
    response = client.get("/")

    text = response.text
    assert isinstance(text, str)
    assert "Hello" in text
