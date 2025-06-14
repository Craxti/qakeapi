import logging

from pydantic import BaseModel

from qakeapi import Application
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response
from qakeapi.security.authorization import IsAdmin, IsAuthenticated, requires_auth
from qakeapi.security.jwt_auth import JWTAuthBackend, JWTConfig

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


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    username: str
    roles: list[str]


async def auth_middleware(request: Request, handler):
    """Middleware to handle JWT authentication"""
    logger.debug(f"Processing request: {request.method} {request.path}")
    logger.debug(f"Headers: {request.headers}")

    auth = None
    for header in request.scope["headers"]:
        if header[0].lower() == b"authorization":
            auth = header[1].decode()
            break

    logger.debug(f"Auth header: {auth}")

    if auth and auth.startswith("Bearer "):
        try:
            user = await auth_backend.authenticate({"token": auth[7:]})
            if user:
                logger.debug(f"User authenticated: {user.username}")
                request.user = user
                return await handler(request)
        except Exception as e:
            logger.error(f"Authentication error: {e}")

    if request.path == "/" or request.path == "/login":
        logger.debug("Allowing access to public endpoint")
        request.user = None
        return await handler(request)

    logger.debug("Authentication required")
    response = Response(content={"detail": "Unauthorized"}, status_code=401)
    response.headers.extend([(b"WWW-Authenticate", b"Bearer")])
    return response


app.add_middleware(auth_middleware)


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
            username=request.user.username, roles=request.user.roles
        ).model_dump()
    )


@app.get("/admin")
@requires_auth(IsAdmin())
async def admin(request: Request) -> Response:
    """Protected endpoint - requires admin role"""
    return Response.json({"message": "Welcome, admin!"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="debug")
