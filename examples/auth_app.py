import logging

from qakeapi.core.application import Application
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response
from qakeapi.security.authentication import BasicAuthBackend
from qakeapi.security.authorization import IsAdmin, IsAuthenticated, requires_auth

from common.auth_models import UserResponse
from common.auth_middleware import create_auth_middleware

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create application
app = Application(
    title="Auth Example", 
    version="1.0.0",
    description="Example application with authentication"
)

# Setup authentication
auth_backend = BasicAuthBackend()
auth_backend.add_user("user", "password123", ["user"])
auth_backend.add_user("admin", "admin123", ["admin", "user"])
logger.debug(f"Initialized auth_backend with users: {auth_backend.users}")

# Add auth middleware
auth_middleware = create_auth_middleware(
    auth_backend=auth_backend,
    public_paths=["/"],
    auth_header_prefix="Basic"
)
app.add_middleware(auth_middleware)

@app.get("/")
async def index(request: Request) -> Response:
    """Public endpoint"""
    return Response.json({"message": "Welcome to the Auth API!"})

@app.get("/profile")
@requires_auth(IsAuthenticated())
async def profile(request: Request) -> Response:
    """Protected endpoint - requires authentication"""
    logger.debug(f"Profile endpoint called with user: {request.user}")
    return Response.json(
        UserResponse(
            username=request.user.username,
            roles=request.user.roles,
            metadata=request.user.metadata
        ).dict()
    )

@app.get("/admin")
@requires_auth(IsAdmin())
async def admin(request: Request) -> Response:
    """Protected endpoint - requires admin role"""
    return Response.json({
        "message": "Welcome, admin!",
        "user": {
            "username": request.user.username,
            "roles": request.user.roles,
            "metadata": request.user.metadata
        }
    })

if __name__ == "__main__":
    import uvicorn
    from config import PORTS
    
    print("Starting auth example server...")
    print("Available routes:", [(r.path, r.type, r.methods) for r in app.router.routes])
    uvicorn.run(app, host="0.0.0.0", port=PORTS['auth_app'], log_level="debug")
