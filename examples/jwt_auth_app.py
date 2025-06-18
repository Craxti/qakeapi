import logging

from qakeapi import Application
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response
from qakeapi.security.authorization import IsAdmin, IsAuthenticated, requires_auth
from qakeapi.security.jwt_auth import JWTAuthBackend, JWTConfig

from common.auth_models import UserResponse, TokenResponse, LoginRequest
from common.auth_middleware import create_auth_middleware

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create application
app = Application(
    title="JWT Auth Example", description="Example application with JWT authentication"
)

# Setup JWT authentication
jwt_config = JWTConfig(
    secret_key="your-secret-key-here",  # In production, use a secure secret key
    access_token_expire_minutes=30,
)
auth_backend = JWTAuthBackend(jwt_config)

# Add some test users
auth_backend.add_user("user", "password123", ["user"])
auth_backend.add_user("admin", "admin123", ["admin", "user"])

# Add auth middleware
app.add_middleware(create_auth_middleware(
    auth_backend=auth_backend,
    public_paths=["/", "/login"],
    auth_header_prefix="Bearer"
))

@app.get("/")
async def index(request: Request) -> Response:
    """Public endpoint"""
    return Response.json({"message": "Welcome to the API!"})

@app.post("/login")
async def login(request: Request) -> Response:
    """Login endpoint - returns JWT token"""
    data = await request.json()
    login_data = LoginRequest(**data)

    user = await auth_backend.authenticate(
        {"username": login_data.username, "password": login_data.password}
    )

    if not user:
        return Response.json({"detail": "Invalid credentials"}, status_code=401)

    token = auth_backend.create_access_token({"sub": user.username})
    return Response.json(
        TokenResponse(access_token=token, token_type="Bearer").model_dump()
    )

@app.get("/profile")
@requires_auth(IsAuthenticated())
async def profile(request: Request) -> Response:
    """Protected endpoint - requires authentication"""
    return Response.json(
        UserResponse(
            username=request.user.username,
            roles=request.user.roles
        ).model_dump()
    )

@app.get("/admin")
@requires_auth(IsAdmin())
async def admin(request: Request) -> Response:
    """Protected endpoint - requires admin role"""
    return Response.json({"message": "Welcome, admin!"})

if __name__ == "__main__":
    import uvicorn
    from config import PORTS
    uvicorn.run(app, host="0.0.0.0", port=PORTS['jwt_auth_app'], log_level="debug")
