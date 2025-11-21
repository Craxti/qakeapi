"""
Enhanced API Documentation Example App

This example demonstrates the enhanced documentation features:
- Interactive Swagger UI with themes
- ReDoc integration
- WebSocket documentation
- Security schemes
- Examples and extended descriptions
"""
import asyncio
import json
from typing import List, Optional
from pydantic import BaseModel, Field

from qakeapi import Application
from qakeapi.core.openapi import (
    OpenAPIInfo, OpenAPIPath, OpenAPIGenerator,
    SecurityScheme, SecuritySchemeType,
    WebSocketDocumentation, WebSocketEvent,
    get_swagger_ui_html, get_redoc_html, get_webSocket_docs_html
)
from qakeapi.core.responses import Response
from qakeapi.core.websockets import WebSocketConnection


# Pydantic models for API documentation
class UserCreate(BaseModel):
    """User creation model"""
    username: str = Field(..., description="Unique username", example="john_doe")
    email: str = Field(..., description="User email address", example="john@example.com")
    full_name: Optional[str] = Field(None, description="Full name", example="John Doe")
    age: Optional[int] = Field(None, ge=0, le=120, description="User age", example=25)


class UserResponse(BaseModel):
    """User response model"""
    id: int = Field(..., description="User ID", example=1)
    username: str = Field(..., description="Username", example="john_doe")
    email: str = Field(..., description="Email", example="john@example.com")
    full_name: Optional[str] = Field(None, description="Full name", example="John Doe")
    age: Optional[int] = Field(None, description="Age", example=25)
    created_at: str = Field(..., description="Creation timestamp", example="2024-01-01T00:00:00Z")


class MessageCreate(BaseModel):
    """Message creation model"""
    content: str = Field(..., description="Message content", example="Hello, world!")
    user_id: int = Field(..., description="User ID", example=1)


class MessageResponse(BaseModel):
    """Message response model"""
    id: int = Field(..., description="Message ID", example=1)
    content: str = Field(..., description="Message content", example="Hello, world!")
    user_id: int = Field(..., description="User ID", example=1)
    created_at: str = Field(..., description="Creation timestamp", example="2024-01-01T00:00:00Z")


class ChatMessage(BaseModel):
    """WebSocket chat message model"""
    type: str = Field(..., description="Message type", example="message")
    content: str = Field(..., description="Message content", example="Hello, everyone!")
    user_id: int = Field(..., description="User ID", example=1)
    timestamp: str = Field(..., description="Message timestamp", example="2024-01-01T00:00:00Z")


# Create application with enhanced documentation
app = Application(title="Enhanced Documentation API", version="1.0.3")

# Create OpenAPI info
info = OpenAPIInfo(
    title="Enhanced Documentation API",
    version="1.0.3",
    description="A comprehensive API with enhanced documentation features",
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "API Support",
        "email": "support@example.com",
        "url": "https://example.com/support"
    },
    license={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {"url": "https://api.example.com", "description": "Production server"},
        {"url": "https://staging-api.example.com", "description": "Staging server"},
        {"url": "http://localhost:8000", "description": "Development server"}
    ]
)

# Initialize OpenAPI generator with enhanced info
openapi_generator = OpenAPIGenerator(info)

# Add security schemes
bearer_scheme = SecurityScheme(
    type=SecuritySchemeType.HTTP,
    name="Authorization",
    description="JWT Bearer token for authentication",
    scheme="bearer",
    bearer_format="JWT"
)

api_key_scheme = SecurityScheme(
    type=SecuritySchemeType.API_KEY,
    name="X-API-Key",
    description="API key for external integrations",
    in_="header"
)

openapi_generator.add_security_scheme("bearerAuth", bearer_scheme)
openapi_generator.add_security_scheme("apiKeyAuth", api_key_scheme)

# Add tags
openapi_generator.add_tag("users", "User management operations")
openapi_generator.add_tag("messages", "Message operations")
openapi_generator.add_tag("websocket", "Real-time WebSocket communication")
openapi_generator.add_tag("auth", "Authentication and authorization")

# Add examples
openapi_generator.add_example(
    "user_create_example",
    "Create User Example",
    "Example of creating a new user",
    {
        "username": "john_doe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "age": 25
    }
)

openapi_generator.add_example(
    "user_response_example",
    "User Response Example",
    "Example of user response",
    {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "age": 25,
        "created_at": "2024-01-01T00:00:00Z"
    }
)

# Add reusable parameters
openapi_generator.add_parameter(
    "user_id_path",
    {
        "name": "user_id",
        "in": "path",
        "required": True,
        "description": "User ID",
        "schema": {"type": "integer", "minimum": 1}
    }
)

# Add reusable responses
openapi_generator.add_response(
    "NotFound",
    {
        "description": "Resource not found",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string", "example": "Resource not found"}
                    }
                }
            }
        }
    }
)


# Mock data storage
users_db = {}
messages_db = {}
user_counter = 1
message_counter = 1


@app.get("/")
async def root(request):
    """Root endpoint with API information"""
    return Response.json({
        "message": "Enhanced Documentation API",
        "version": "1.0.3",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "websocket_docs": "/websocket-docs"
        }
    })


@app.post("/users")
async def create_user(request):
    """Create a new user"""
    # Parse request body
    body = await request.json()
    user_data = UserCreate(**body)
    
    global user_counter
    user_id = user_counter
    user_counter += 1
    
    # Create user
    user = UserResponse(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        age=user_data.age,
        created_at="2024-01-01T00:00:00Z"
    )
    
    users_db[user_id] = user.dict()
    
    return Response.json(user.dict(), status_code=201)


@app.get("/users/{user_id}")
async def get_user(request, user_id: int):
    """Get user by ID"""
    if user_id not in users_db:
        return Response.json({"detail": "User not found"}, status_code=404)
    
    user = users_db[user_id]
    return Response.json(user)


@app.get("/users")
async def list_users(request):
    """List all users"""
    users = list(users_db.values())
    return Response.json(users)


@app.post("/messages")
async def create_message(request):
    """Create a new message"""
    body = await request.json()
    message_data = MessageCreate(**body)
    
    global message_counter
    message_id = message_counter
    message_counter += 1
    
    message = MessageResponse(
        id=message_id,
        content=message_data.content,
        user_id=message_data.user_id,
        created_at="2024-01-01T00:00:00Z"
    )
    
    messages_db[message_id] = message.dict()
    
    return Response.json(message.dict(), status_code=201)


@app.get("/messages")
async def list_messages(request):
    """List all messages"""
    messages = list(messages_db.values())
    return Response.json(messages)


@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocketConnection):
    """Real-time chat WebSocket endpoint"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Echo back with timestamp
            response = ChatMessage(
                type="message",
                content=message_data.get("content", ""),
                user_id=message_data.get("user_id", 0),
                timestamp="2024-01-01T00:00:00Z"
            )
            
            await websocket.send_text(response.model_dump_json())
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@app.get("/docs")
async def swagger_ui(request):
    """Serve Swagger UI"""
    html = get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Enhanced API Documentation - Swagger UI",
        theme="default"
    )
    return Response.html(html)


@app.get("/docs/dark")
async def swagger_ui_dark(request):
    """Serve Swagger UI with dark theme"""
    html = get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Enhanced API Documentation - Swagger UI (Dark)",
        theme="dark"
    )
    return Response.html(html)


@app.get("/redoc")
async def redoc_ui(request):
    """Serve ReDoc UI"""
    html = get_redoc_html(
        openapi_url="/openapi.json",
        title="Enhanced API Documentation - ReDoc"
    )
    return Response.html(html)


@app.get("/websocket-docs")
async def websocket_docs(request):
    """Serve WebSocket documentation"""
    # Create WebSocket documentation
    chat_event = WebSocketEvent(
        name="message",
        description="Chat message event",
        payload_schema=ChatMessage,
        examples=[
            {
                "type": "message",
                "content": "Hello, everyone!",
                "user_id": 1,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
    )
    
    ws_doc = WebSocketDocumentation(
        path="/ws/chat",
        description="Real-time chat WebSocket endpoint for messaging",
        events=[chat_event],
        security=[{"bearerAuth": []}]
    )
    
    html = get_webSocket_docs_html([ws_doc])
    return Response.html(html)


@app.get("/openapi.json")
async def openapi_schema(request):
    """Serve OpenAPI schema"""
    # Add paths to OpenAPI generator
    paths = [
        OpenAPIPath(
            path="/",
            method="GET",
            summary="Root endpoint",
            description="Get API information and documentation links",
            tags=["info"],
            operation_id="get_root"
        ),
        OpenAPIPath(
            path="/users",
            method="POST",
            summary="Create user",
            description="Create a new user account",
            request_model=UserCreate,
            response_model=UserResponse,
            tags=["users"],
            operation_id="create_user",
            examples=[
                {
                    "summary": "Create User Example",
                    "description": "Example of creating a new user",
                    "value": {
                        "username": "john_doe",
                        "email": "john@example.com",
                        "full_name": "John Doe",
                        "age": 25
                    }
                }
            ]
        ),
        OpenAPIPath(
            path="/users/{user_id}",
            method="GET",
            summary="Get user",
            description="Get user by ID",
            response_model=UserResponse,
            tags=["users"],
            operation_id="get_user",
            parameters=[
                {
                    "name": "user_id",
                    "in": "path",
                    "required": True,
                    "description": "User ID",
                    "schema": {"type": "integer", "minimum": 1}
                }
            ],
            responses={
                "404": {"$ref": "#/components/responses/NotFound"}
            }
        ),
        OpenAPIPath(
            path="/users",
            method="GET",
            summary="List users",
            description="Get all users",
            tags=["users"],
            operation_id="list_users"
        ),
        OpenAPIPath(
            path="/messages",
            method="POST",
            summary="Create message",
            description="Create a new message",
            request_model=MessageCreate,
            response_model=MessageResponse,
            tags=["messages"],
            operation_id="create_message",
            security=[{"bearerAuth": []}]
        ),
        OpenAPIPath(
            path="/messages",
            method="GET",
            summary="List messages",
            description="Get all messages",
            tags=["messages"],
            operation_id="list_messages",
            security=[{"bearerAuth": []}]
        )
    ]
    
    for path in paths:
        openapi_generator.add_path(path)
    
    # Add WebSocket documentation
    chat_event = WebSocketEvent(
        name="message",
        description="Chat message event",
        payload_schema=ChatMessage,
        examples=[
            {
                "type": "message",
                "content": "Hello, everyone!",
                "user_id": 1,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
    )
    
    ws_doc = WebSocketDocumentation(
        path="/ws/chat",
        description="Real-time chat WebSocket endpoint for messaging",
        events=[chat_event],
        security=[{"bearerAuth": []}]
    )
    
    openapi_generator.add_webSocket_documentation(ws_doc)
    
    schema = openapi_generator.generate()
    return Response.json(schema)


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Enhanced Documentation API Example")
    print("=" * 50)
    print("Available endpoints:")
    print("  📖 Swagger UI: http://localhost:8022/docs")
    print("  🌙 Swagger UI (Dark): http://localhost:8022/docs/dark")
    print("  📚 ReDoc: http://localhost:8022/redoc")
    print("  🔌 WebSocket Docs: http://localhost:8022/websocket-docs")
    print("  📋 OpenAPI Schema: http://localhost:8022/openapi.json")
    print("  🏠 API Root: http://localhost:8022/")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8022) 