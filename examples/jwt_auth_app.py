import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, List, Dict, Any, Callable, Awaitable

from qakeapi.core.application import Application
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response, JSONResponse
from qakeapi.security.authentication import JWTAuthBackend, JWTConfig
from qakeapi.security.authorization import requires_auth
import jwt

from config import PORTS

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='jwt_auth.log'
)
logger = logging.getLogger(__name__)

# Create application
app = Application()

# JWT configuration
JWT_SECRET = "your-secret-key"
JWT_ALGORITHM = "HS256"

# Mock users database
USERS = {
    "user": {
        "password": "password",
        "roles": ["user"]
    },
    "admin": {
        "password": "admin",
        "roles": ["admin", "user"]
    }
}

auth_backend = JWTAuthBackend(config=JWTConfig(
    secret_key=JWT_SECRET,
    algorithm=JWT_ALGORITHM,
    access_token_expire_minutes=30
))
for username, data in USERS.items():
    auth_backend.add_user(username, data["password"], data["roles"])

# Set auth backend for the application
app.auth_backend = auth_backend

JWT_AUTH_PORT = 8008  # Используем фиксированный порт

def check_roles(roles: List[str]) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Response:
            # Get token from header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    content={"detail": "Invalid authentication credentials"},
                    status_code=401
                )
            
            token = auth_header.split(" ")[1]
            
            try:
                # Verify token and check roles
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                user_roles = payload.get("roles", [])
                
                if not any(role in user_roles for role in roles):
                    return JSONResponse(
                        content={"detail": "Insufficient permissions"},
                        status_code=403
                    )
                
                return await func(request, *args, **kwargs)
            except jwt.ExpiredSignatureError:
                return JSONResponse(
                    content={"detail": "Token has expired"},
                    status_code=401
                )
            except jwt.InvalidTokenError:
                return JSONResponse(
                    content={"detail": "Invalid token"},
                    status_code=401
                )
        return wrapper
    return decorator

def requires_auth(func: Callable) -> Callable:
    return check_roles(["user"])(func)

@app.get("/")
async def index(request: Request) -> Response:
    try:
        return JSONResponse(
            content={"message": "JWT auth example server is running"},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error in index: {str(e)}")
        return JSONResponse(
            content={"detail": str(e)},
            status_code=500
        )

@app.post("/login")
async def login(request: Request) -> Response:
    try:
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            return JSONResponse(
                content={"detail": "Missing username or password"},
                status_code=400
            )
        
        # Authenticate user
        if username not in USERS or USERS[username]["password"] != password:
            return JSONResponse(
                content={"detail": "Invalid credentials"},
                status_code=401
            )
        
        # Generate token
        token = jwt.encode(
            {
                "sub": username,
                "roles": USERS[username]["roles"],
                "exp": datetime.now() + timedelta(days=1)
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )
        
        return JSONResponse(
            content={"access_token": token, "token_type": "bearer"},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        return JSONResponse(
            content={"detail": str(e)},
            status_code=500
        )

@app.get("/protected")
@requires_auth
async def protected(request: Request) -> Response:
    try:
        return JSONResponse(
            content={"message": "This is a protected endpoint"},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error in protected: {str(e)}")
        return JSONResponse(
            content={"detail": str(e)},
            status_code=500
        )

@app.get("/admin")
@requires_auth
@check_roles(["admin"])
async def admin(request: Request) -> Response:
    try:
        return JSONResponse(
            content={"message": "This is an admin endpoint"},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error in admin: {str(e)}")
        return JSONResponse(
            content={"detail": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    print("Starting JWT auth example server...")
    uvicorn.run(app, host="0.0.0.0", port=JWT_AUTH_PORT)
