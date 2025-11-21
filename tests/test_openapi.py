"""
Tests for OpenAPI generation.
"""

import pytest
import json
from qakeapi import QakeAPI
from qakeapi.core.openapi import OpenAPIGenerator


def test_openapi_generator():
    """Test OpenAPI generator."""
    generator = OpenAPIGenerator(
        title="Test API",
        version="1.0.0",
        description="Test API description",
    )
    
    from qakeapi.core.router import Router
    
    router = Router()
    
    def handler(request):
        return {"message": "test"}
    
    router.add_route("/test", handler, ["GET"])
    router.add_route("/users/{user_id}", handler, ["GET", "POST"])
    
    schema = generator.generate_schema(router)
    
    assert schema["openapi"] == "3.0.0"
    assert schema["info"]["title"] == "Test API"
    assert schema["info"]["version"] == "1.0.0"
    assert "paths" in schema
    assert "/test" in schema["paths"]
    assert "/users/{user_id}" in schema["paths"]


def test_openapi_path_parameters():
    """Test OpenAPI path parameters."""
    generator = OpenAPIGenerator()
    
    from qakeapi.core.router import Router
    
    router = Router()
    
    def handler(request):
        return {}
    
    router.add_route("/users/{user_id}/posts/{post_id}", handler, ["GET"])
    
    schema = generator.generate_schema(router)
    
    path = schema["paths"]["/users/{user_id}/posts/{post_id}"]
    operation = path["get"]
    
    assert "parameters" in operation
    assert len(operation["parameters"]) == 2
    assert operation["parameters"][0]["name"] == "user_id"
    assert operation["parameters"][1]["name"] == "post_id"


def test_openapi_json_output():
    """Test OpenAPI JSON output."""
    generator = OpenAPIGenerator(title="Test API")
    
    from qakeapi.core.router import Router
    
    router = Router()
    
    def handler(request):
        return {}
    
    router.add_route("/test", handler, ["GET"])
    
    json_output = generator.to_json(router)
    schema = json.loads(json_output)
    
    assert schema["openapi"] == "3.0.0"
    assert schema["info"]["title"] == "Test API"


@pytest.mark.asyncio
async def test_app_openapi_endpoint():
    """Test OpenAPI endpoint in application."""
    app = QakeAPI(title="Test API", version="1.0.0")
    
    @app.get("/test")
    async def test_handler(request):
        return {"message": "test"}
    
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/openapi.json",
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
    
    # Check response
    assert len(messages) >= 2
    assert messages[0]["type"] == "http.response.start"
    assert messages[0]["status"] == 200
    
    # Check body contains OpenAPI schema
    body = messages[1]["body"]
    schema = json.loads(body.decode())
    assert schema["openapi"] == "3.0.0"
    assert schema["info"]["title"] == "Test API"

