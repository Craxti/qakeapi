"""
Dependency Injection example.

Demonstrates:
- Using Depends for dependencies
- Dependency caching
- Type conversion in dependencies
"""

from qakeapi import QakeAPI, Request, Depends
from qakeapi.security import AuthManager


app = QakeAPI(title="Dependency Injection Example")
auth_manager = AuthManager(secret_key="secret-key")


async def get_database():
    """Database dependency."""
    # In real app, return database connection
    return {"type": "database", "connected": True}


async def get_current_user(
    request: Request,
    db: dict = Depends(get_database),
):
    """Get current user from request."""
    # Extract token from header
    auth_header = request.headers.get("authorization", "")
    
    if not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header[7:]
    user_data = auth_manager.verify_token(token)
    
    return user_data


async def require_auth(current_user: dict = Depends(get_current_user)):
    """Require authentication."""
    if current_user is None:
        from qakeapi.core.exceptions import HTTPException
        raise HTTPException(401, "Authentication required")
    return current_user


@app.get("/")
async def root(db: dict = Depends(get_database)):
    """Root endpoint with database dependency."""
    return {
        "message": "Hello",
        "database": db,
    }


@app.get("/profile")
async def get_profile(user: dict = Depends(require_auth)):
    """Get user profile (requires auth)."""
    return {"user": user}


@app.get("/public")
async def public_endpoint():
    """Public endpoint (no auth required)."""
    return {"message": "This is public"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

