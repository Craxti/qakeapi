import base64
import logging

from pydantic import BaseModel

from qakeapi import Application
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response
from qakeapi.security.authentication import BasicAuthBackend, User
from qakeapi.security.authorization import IsAdmin, IsAuthenticated, requires_auth

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create application
app = Application(
    title="Auth Example", description="Example application with authentication"
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
    logger.debug(f"Processing request: {request.method} {request.path}")
    logger.debug(f"Headers: {request.headers}")

    auth = None
    for header in request.scope["headers"]:
        if header[0].lower() == b"authorization":
            auth = header[1].decode()
            break

    logger.debug(f"Auth header: {auth}")

    if auth and auth.startswith("Basic "):
        try:
            decoded = base64.b64decode(auth[6:]).decode()
            username, password = decoded.split(":")
            logger.debug(f"Attempting to authenticate user: {username}")

            credentials = {"username": username, "password": password}
            user = await auth_backend.authenticate(credentials)

            if user:
                logger.debug(f"User authenticated: {user.username}")
                request.user = user
                return await handler(request)
        except Exception as e:
            logger.error(f"Authentication error: {e}")

    if request.path == "/":
        logger.debug("Allowing access to public endpoint")
        request.user = None
        return await handler(request)

    logger.debug("Authentication required")
    response = Response(content={"detail": "Unauthorized"}, status_code=401)
    response.headers.extend([(b"WWW-Authenticate", b"Basic")])
    return response


app.add_middleware(auth_middleware)


@app.get("/")
async def index(request: Request) -> Response:
    """Public endpoint"""
    return Response.json({"message": "Welcome to the API!"})


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
    from config import PORTS
    uvicorn.run(app, host="0.0.0.0", port=PORTS['auth_app'], log_level="debug")
