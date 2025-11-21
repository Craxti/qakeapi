"""
Tests for enhanced API documentation features.
"""

import json

import pytest
from pydantic import BaseModel, Field

from qakeapi.core.openapi import (
    OpenAPIGenerator,
    OpenAPIInfo,
    OpenAPIPath,
    SecurityScheme,
    SecuritySchemeType,
    WebSocketDocumentation,
    WebSocketEvent,
    get_redoc_html,
    get_swagger_ui_html,
    get_webSocket_docs_html,
)


class TestModel(BaseModel):
    """Test model for documentation"""

    name: str = Field(..., description="Test name", example="test")
    value: int = Field(..., description="Test value", example=42)


class TestResponseModel(BaseModel):
    """Test response model"""

    id: int = Field(..., description="ID", example=1)
    name: str = Field(..., description="Name", example="test")
    value: int = Field(..., description="Value", example=42)


class TestWebSocketMessage(BaseModel):
    """Test WebSocket message model"""

    type: str = Field(..., description="Message type", example="test")
    data: str = Field(..., description="Message data", example="hello")


class TestEnhancedDocumentation:
    """Test enhanced documentation features"""

    def test_enhanced_openapi_info(self):
        """Test enhanced OpenAPI info"""
        info = OpenAPIInfo(
            title="Test API",
            version="1.0.0",
            description="Test description",
            terms_of_service="https://example.com/terms",
            contact={"name": "Test", "email": "test@example.com"},
            license={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
            servers=[{"url": "http://localhost:8000", "description": "Local"}],
        )

        assert info.title == "Test API"
        assert info.version == "1.0.0"
        assert info.description == "Test description"
        assert info.terms_of_service == "https://example.com/terms"
        assert info.contact["name"] == "Test"
        assert info.license["name"] == "MIT"
        assert len(info.servers) == 1

    def test_enhanced_openapi_path(self):
        """Test enhanced OpenAPI path"""
        path = OpenAPIPath(
            path="/test",
            method="POST",
            summary="Test endpoint",
            description="Test description",
            request_model=TestModel,
            response_model=TestResponseModel,
            tags=["test"],
            security=[{"bearerAuth": []}],
            examples=[{"summary": "Test", "value": {"name": "test", "value": 42}}],
            deprecated=False,
            operation_id="test_operation",
            parameters=[{"name": "test", "in": "query", "schema": {"type": "string"}}],
            responses={"400": {"description": "Bad request"}},
        )

        assert path.path == "/test"
        assert path.method == "POST"
        assert path.summary == "Test endpoint"
        assert path.tags == ["test"]
        assert path.security == [{"bearerAuth": []}]
        assert len(path.examples) == 1
        assert path.operation_id == "test_operation"
        assert len(path.parameters) == 1
        assert "400" in path.responses

    def test_security_scheme(self):
        """Test security scheme"""
        scheme = SecurityScheme(
            type=SecuritySchemeType.HTTP,
            name="Authorization",
            description="Bearer token",
            scheme="bearer",
            bearer_format="JWT",
        )

        assert scheme.type == SecuritySchemeType.HTTP
        assert scheme.name == "Authorization"
        assert scheme.description == "Bearer token"
        assert scheme.scheme == "bearer"
        assert scheme.bearer_format == "JWT"

    def test_websocket_event(self):
        """Test WebSocket event"""
        event = WebSocketEvent(
            name="test_event",
            description="Test event",
            payload_schema=TestWebSocketMessage,
            examples=[{"type": "test", "data": "hello"}],
        )

        assert event.name == "test_event"
        assert event.description == "Test event"
        assert event.payload_schema == TestWebSocketMessage
        assert len(event.examples) == 1

    def test_websocket_documentation(self):
        """Test WebSocket documentation"""
        event = WebSocketEvent(
            name="test_event",
            description="Test event",
            payload_schema=TestWebSocketMessage,
        )

        ws_doc = WebSocketDocumentation(
            path="/ws/test",
            description="Test WebSocket",
            events=[event],
            security=[{"bearerAuth": []}],
        )

        assert ws_doc.path == "/ws/test"
        assert ws_doc.description == "Test WebSocket"
        assert len(ws_doc.events) == 1
        assert ws_doc.security == [{"bearerAuth": []}]

    def test_enhanced_openapi_generator(self):
        """Test enhanced OpenAPI generator"""
        info = OpenAPIInfo(title="Test API", version="1.0.0")
        generator = OpenAPIGenerator(info)

        # Add security scheme
        scheme = SecurityScheme(
            type=SecuritySchemeType.HTTP,
            name="Authorization",
            description="Bearer token",
            scheme="bearer",
        )
        generator.add_security_scheme("bearerAuth", scheme)

        # Add tag
        generator.add_tag("test", "Test operations")

        # Add example
        generator.add_example("test_example", "Test", "Test example", {"test": "value"})

        # Add parameter
        generator.add_parameter(
            "test_param", {"name": "test", "in": "query", "schema": {"type": "string"}}
        )

        # Add response
        generator.add_response(
            "TestResponse",
            {
                "description": "Test response",
                "content": {"application/json": {"schema": {"type": "object"}}},
            },
        )

        # Add path
        path = OpenAPIPath(
            path="/test", method="GET", summary="Test endpoint", tags=["test"]
        )
        generator.add_path(path)

        # Add WebSocket documentation
        event = WebSocketEvent(name="test", description="Test")
        ws_doc = WebSocketDocumentation(path="/ws/test", events=[event])
        generator.add_webSocket_documentation(ws_doc)

        # Generate schema
        schema = generator.generate()

        assert schema["openapi"] == "3.1.0"
        assert schema["info"]["title"] == "Test API"
        assert "bearerAuth" in schema["components"]["securitySchemes"]
        assert len(schema["tags"]) == 1
        assert "test_example" in schema["components"]["examples"]
        assert "test_param" in schema["components"]["parameters"]
        assert "TestResponse" in schema["components"]["responses"]
        assert "/test" in schema["paths"]
        assert "security" in schema

        # Test WebSocket docs
        ws_docs = generator.generate_webSocket_docs()
        assert "webSocket" in ws_docs
        assert len(ws_docs["webSocket"]["endpoints"]) == 1

    def test_swagger_ui_html_generation(self):
        """Test Swagger UI HTML generation"""
        html = get_swagger_ui_html(
            openapi_url="/openapi.json", title="Test API", theme="default"
        )

        assert "swagger-ui" in html
        assert "/openapi.json" in html
        assert "Test API" in html
        assert "SwaggerUIBundle" in html

    def test_swagger_ui_dark_theme(self):
        """Test Swagger UI dark theme"""
        html = get_swagger_ui_html(
            openapi_url="/openapi.json", title="Test API", theme="dark"
        )

        assert "background-color: #1a1a1a" in html
        assert "color: #ffffff" in html

    def test_swagger_ui_custom_css(self):
        """Test Swagger UI with custom CSS"""
        custom_css = ".custom-class { color: red; }"
        html = get_swagger_ui_html(
            openapi_url="/openapi.json", title="Test API", custom_css=custom_css
        )

        assert custom_css in html

    def test_redoc_html_generation(self):
        """Test ReDoc HTML generation"""
        html = get_redoc_html(openapi_url="/openapi.json", title="Test API")

        assert "redoc" in html
        assert "/openapi.json" in html
        assert "Test API" in html
        assert "Redoc.init" in html

    def test_redoc_custom_theme(self):
        """Test ReDoc with custom theme"""
        theme = {"colors": {"primary": {"main": "#ff0000"}}}
        html = get_redoc_html(
            openapi_url="/openapi.json", title="Test API", theme=theme
        )

        assert "#ff0000" in html

    def test_websocket_docs_html_generation(self):
        """Test WebSocket documentation HTML generation"""
        event = WebSocketEvent(
            name="test_event",
            description="Test event",
            payload_schema=TestWebSocketMessage,
            examples=[{"type": "test", "data": "hello"}],
        )

        ws_doc = WebSocketDocumentation(
            path="/ws/test", description="Test WebSocket", events=[event]
        )

        html = get_webSocket_docs_html([ws_doc])

        assert "WebSocket Documentation" in html
        assert "/ws/test" in html
        assert "test_event" in html
        assert "Test event" in html
        assert "test" in html  # Example data

    def test_websocket_docs_multiple_events(self):
        """Test WebSocket documentation with multiple events"""
        event1 = WebSocketEvent(
            name="event1",
            description="First event",
            payload_schema=TestWebSocketMessage,
        )

        event2 = WebSocketEvent(
            name="event2",
            description="Second event",
            payload_schema=TestWebSocketMessage,
        )

        ws_doc = WebSocketDocumentation(
            path="/ws/test", description="Test WebSocket", events=[event1, event2]
        )

        html = get_webSocket_docs_html([ws_doc])

        assert "event1" in html
        assert "event2" in html
        assert "First event" in html
        assert "Second event" in html

    def test_websocket_docs_multiple_endpoints(self):
        """Test WebSocket documentation with multiple endpoints"""
        event1 = WebSocketEvent(name="event1", description="Event 1")
        event2 = WebSocketEvent(name="event2", description="Event 2")

        ws_doc1 = WebSocketDocumentation(
            path="/ws/test1", description="Test WebSocket 1", events=[event1]
        )

        ws_doc2 = WebSocketDocumentation(
            path="/ws/test2", description="Test WebSocket 2", events=[event2]
        )

        html = get_webSocket_docs_html([ws_doc1, ws_doc2])

        assert "/ws/test1" in html
        assert "/ws/test2" in html
        assert "Test WebSocket 1" in html
        assert "Test WebSocket 2" in html
        assert "event1" in html
        assert "event2" in html

    def test_openapi_schema_with_components(self):
        """Test OpenAPI schema generation with components"""
        info = OpenAPIInfo(title="Test API", version="1.0.0")
        generator = OpenAPIGenerator(info)

        # Add various components
        generator.add_security_scheme(
            "bearerAuth",
            SecurityScheme(
                type=SecuritySchemeType.HTTP, name="Authorization", scheme="bearer"
            ),
        )

        generator.add_tag("users", "User operations")
        generator.add_tag("messages", "Message operations")

        generator.add_example(
            "user_example", "User", "User example", {"id": 1, "name": "John Doe"}
        )

        generator.add_parameter(
            "user_id",
            {
                "name": "user_id",
                "in": "path",
                "required": True,
                "schema": {"type": "integer"},
            },
        )

        generator.add_response(
            "UserResponse",
            {
                "description": "User response",
                "content": {
                    "application/json": {
                        "schema": TestResponseModel.model_json_schema()
                    }
                },
            },
        )

        # Add path with components
        path = OpenAPIPath(
            path="/users/{user_id}",
            method="GET",
            summary="Get user",
            tags=["users"],
            parameters=[{"$ref": "#/components/parameters/user_id"}],
            responses={"200": {"$ref": "#/components/responses/UserResponse"}},
        )
        generator.add_path(path)

        schema = generator.generate()

        # Verify components
        assert "securitySchemes" in schema["components"]
        assert "bearerAuth" in schema["components"]["securitySchemes"]
        assert len(schema["tags"]) == 2
        assert "user_example" in schema["components"]["examples"]
        assert "user_id" in schema["components"]["parameters"]
        assert "UserResponse" in schema["components"]["responses"]

        # Verify path references
        path_data = schema["paths"]["/users/{user_id}"]["get"]
        assert path_data["parameters"][0]["$ref"] == "#/components/parameters/user_id"
        assert (
            path_data["responses"]["200"]["$ref"]
            == "#/components/responses/UserResponse"
        )

    def test_openapi_schema_with_servers(self):
        """Test OpenAPI schema with multiple servers"""
        info = OpenAPIInfo(
            title="Test API",
            version="1.0.0",
            servers=[
                {"url": "http://localhost:8000", "description": "Development"},
                {"url": "https://api.example.com", "description": "Production"},
            ],
        )
        generator = OpenAPIGenerator(info)

        schema = generator.generate()

        assert "servers" in schema
        assert len(schema["servers"]) == 2
        assert schema["servers"][0]["url"] == "http://localhost:8000"
        assert schema["servers"][1]["url"] == "https://api.example.com"

    def test_openapi_schema_with_contact_and_license(self):
        """Test OpenAPI schema with contact and license info"""
        info = OpenAPIInfo(
            title="Test API",
            version="1.0.0",
            contact={
                "name": "API Support",
                "email": "support@example.com",
                "url": "https://example.com/support",
            },
            license={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
        )
        generator = OpenAPIGenerator(info)

        schema = generator.generate()

        assert "contact" in schema["info"]
        assert schema["info"]["contact"]["name"] == "API Support"
        assert schema["info"]["contact"]["email"] == "support@example.com"

        assert "license" in schema["info"]
        assert schema["info"]["license"]["name"] == "MIT"
        assert schema["info"]["license"]["url"] == "https://opensource.org/licenses/MIT"


class TestSecuritySchemes:
    """Test security schemes"""

    def test_http_bearer_scheme(self):
        """Test HTTP Bearer security scheme"""
        scheme = SecurityScheme(
            type=SecuritySchemeType.HTTP,
            name="Authorization",
            description="Bearer token",
            scheme="bearer",
            bearer_format="JWT",
        )

        info = OpenAPIInfo(title="Test API", version="1.0.0")
        generator = OpenAPIGenerator(info)
        generator.add_security_scheme("bearerAuth", scheme)

        schema = generator.generate()
        scheme_data = schema["components"]["securitySchemes"]["bearerAuth"]

        assert scheme_data["type"] == "http"
        assert scheme_data["scheme"] == "bearer"
        assert scheme_data["bearerFormat"] == "JWT"
        assert scheme_data["description"] == "Bearer token"

    def test_api_key_scheme(self):
        """Test API Key security scheme"""
        scheme = SecurityScheme(
            type=SecuritySchemeType.API_KEY,
            name="X-API-Key",
            description="API key",
            in_="header",
        )

        info = OpenAPIInfo(title="Test API", version="1.0.0")
        generator = OpenAPIGenerator(info)
        generator.add_security_scheme("apiKeyAuth", scheme)

        schema = generator.generate()
        scheme_data = schema["components"]["securitySchemes"]["apiKeyAuth"]

        assert scheme_data["type"] == "apiKey"
        assert scheme_data["name"] == "X-API-Key"
        assert scheme_data["in"] == "header"
        assert scheme_data["description"] == "API key"

    def test_oauth2_scheme(self):
        """Test OAuth2 security scheme"""
        flows = {
            "authorizationCode": {
                "authorizationUrl": "https://example.com/oauth/authorize",
                "tokenUrl": "https://example.com/oauth/token",
                "scopes": {"read": "Read access", "write": "Write access"},
            }
        }

        scheme = SecurityScheme(
            type=SecuritySchemeType.OAUTH2,
            name="OAuth2",
            description="OAuth2 authentication",
            flows=flows,
        )

        info = OpenAPIInfo(title="Test API", version="1.0.0")
        generator = OpenAPIGenerator(info)
        generator.add_security_scheme("oauth2Auth", scheme)

        schema = generator.generate()
        scheme_data = schema["components"]["securitySchemes"]["oauth2Auth"]

        assert scheme_data["type"] == "oauth2"
        assert "flows" in scheme_data
        assert "authorizationCode" in scheme_data["flows"]
        assert "read" in scheme_data["flows"]["authorizationCode"]["scopes"]


class TestWebSocketDocumentation:
    """Test WebSocket documentation features"""

    def test_websocket_event_with_schema(self):
        """Test WebSocket event with Pydantic schema"""
        event = WebSocketEvent(
            name="chat_message",
            description="Chat message event",
            payload_schema=TestWebSocketMessage,
            examples=[
                {"type": "message", "data": "Hello!"},
                {"type": "notification", "data": "User joined"},
            ],
        )

        assert event.name == "chat_message"
        assert event.description == "Chat message event"
        assert event.payload_schema == TestWebSocketMessage
        assert len(event.examples) == 2

    def test_websocket_documentation_generation(self):
        """Test WebSocket documentation generation"""
        event1 = WebSocketEvent(
            name="message",
            description="Chat message",
            payload_schema=TestWebSocketMessage,
        )

        event2 = WebSocketEvent(
            name="join", description="User joined", payload_schema=TestWebSocketMessage
        )

        ws_doc = WebSocketDocumentation(
            path="/ws/chat",
            description="Real-time chat WebSocket",
            events=[event1, event2],
            security=[{"bearerAuth": []}],
        )

        info = OpenAPIInfo(title="Test API", version="1.0.0")
        generator = OpenAPIGenerator(info)
        generator.add_webSocket_documentation(ws_doc)

        ws_docs = generator.generate_webSocket_docs()

        assert "webSocket" in ws_docs
        assert len(ws_docs["webSocket"]["endpoints"]) == 1

        endpoint = ws_docs["webSocket"]["endpoints"][0]
        assert endpoint["path"] == "/ws/chat"
        assert endpoint["description"] == "Real-time chat WebSocket"
        assert len(endpoint["events"]) == 2
        assert endpoint["security"] == [{"bearerAuth": []}]

        # Check events
        events = endpoint["events"]
        assert events[0]["name"] == "message"
        assert events[1]["name"] == "join"
        assert events[0]["payload_schema"] is not None
        assert events[1]["payload_schema"] is not None
