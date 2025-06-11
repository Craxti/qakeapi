from qakeapi import Application
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response
from qakeapi.security.authentication import BasicAuthBackend
from qakeapi.security.authorization import IsAuthenticated, IsAdmin, requires_auth
from pydantic import BaseModel

# Create application
app = Application(
    title="Auth Example",
    description="Example application with authentication"
)

# Setup authentication
auth_backend = BasicAuthBackend()
auth_backend.add_user("user", "password123", ["user"])
auth_backend.add_user("admin", "admin123", ["admin", "user"])

class UserResponse(BaseModel):
    username: str
    roles: list[str]

async def auth_middleware(request: Request, handler):
    """Middleware to handle authentication"""
    user = await auth_backend.authenticate(request)
    request.user = user
    return await handler(request)

app.add_middleware(auth_middleware)

@app.get("/")
async def index(request: Request) -> Response:
    """Public endpoint"""
    return Response.json({"message": "Welcome to the API!"})

@app.get("/profile")
@requires_auth(IsAuthenticated())
async def profile(request: Request) -> Response:
    """Protected endpoint - requires authentication"""
    return Response.json(UserResponse(
        username=request.user.username,
        roles=request.user.roles
    ).model_dump())

@app.get("/admin")
@requires_auth(IsAdmin())
async def admin(request: Request) -> Response:
    """Protected endpoint - requires admin role"""
    return Response.json({"message": "Welcome, admin!"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 