"""
QakeAPI Authentication and Authorization Example.

Demonstrates:
- Authentication system initialization
- JWT token creation
- @require_auth decorator
- @require_role decorator
- Session management
"""

from qakeapi import (
    QakeAPI,
    Request,
    JSONResponse,
    init_auth,
    require_auth,
    require_role,
    create_token,
    create_session,
    get_session,
    delete_session,
)
import secrets
import uuid

app = QakeAPI(
    title="QakeAPI - Authentication and Authorization",
    version="1.2.0",
    description="Authentication and authorization usage example",
    debug=True,
)

# Initialize authentication system
# In production, use a secure secret key!
SECRET_KEY = secrets.token_urlsafe(32)
init_auth(
    secret_key=SECRET_KEY,
    jwt_expiration=3600,  # 1 hour
    session_timeout=7200,  # 2 hours
)

# Simple user database (use a real database in production)
USERS = {
    "admin": {
        "id": 1,
        "username": "admin",
        "password": "admin123",  # In production, use password hashing!
        "email": "admin@example.com",
        "roles": ["admin", "user"],
    },
    "user": {
        "id": 2,
        "username": "user",
        "password": "user123",
        "email": "user@example.com",
        "roles": ["user"],
    },
    "manager": {
        "id": 3,
        "username": "manager",
        "password": "manager123",
        "email": "manager@example.com",
        "roles": ["manager", "user"],
    },
}


# Login route (get token)
@app.post("/login")
async def login(request: Request):
    """
    User login and JWT token retrieval.
    
    Body:
        {
            "username": "admin",
            "password": "admin123"
        }
    """
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return JSONResponse(
            {"error": "Username and password required"},
            status_code=400
        )
    
    # Verify user
    user = USERS.get(username)
    if not user or user["password"] != password:
        return JSONResponse(
            {"error": "Invalid username or password"},
            status_code=401
        )
    
    # Create JWT token
    payload = {
        "user_id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "roles": user["roles"],
    }
    token = create_token(payload, expires_in=3600)
    
    # Create session (optional)
    session_id = str(uuid.uuid4())
    create_session(session_id, {
        "user_id": user["id"],
        "username": user["username"],
        "login_time": __import__("time").time(),
    })
    
    return JSONResponse({
        "message": "Login successful",
        "token": token,
        "session_id": session_id,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "roles": user["roles"],
        },
    })


# Public route (no authentication required)
@app.get("/")
def public():
    """Public page."""
    return {"message": "Welcome! Use /login to authenticate."}


# Protected route (requires authentication)
@app.get("/profile")
@require_auth()
async def get_profile(request: Request, user: dict):
    """
    Get current user profile.
    
    Requires: Authorization header: Bearer <token>
    """
    return {
        "message": "User profile",
        "user": user,
    }


# Route only for users with "admin" role
@app.get("/admin")
@require_auth()
@require_role("admin")
async def admin_panel(request: Request, user: dict):
    """
    Admin panel.
    
    Requires:
        - Authorization header: Bearer <token>
        - Role: admin
    """
    return {
        "message": "Welcome to admin panel!",
        "user": user,
    }


# Route for managers and admins
@app.get("/management")
@require_auth()
@require_role("manager", "admin")
async def management_panel(request: Request, user: dict):
    """
    Management panel.
    
    Requires:
        - Authorization header: Bearer <token>
        - Role: manager or admin
    """
    return {
        "message": "Management panel",
        "user": user,
    }


# Route for session management
@app.get("/session/{session_id}")
def get_session_info(session_id: str):
    """
    Get session information.
    
    Args:
        session_id: Session ID
    """
    session = get_session(session_id)
    if not session:
        return JSONResponse(
            {"error": "Session not found or expired"},
            status_code=404
        )
    
    return {
        "session": session,
    }


# Logout route (delete session)
@app.post("/logout")
async def logout(request: Request):
    """
    User logout (delete session).
    
    Body (optional):
        {
            "session_id": "session-uuid"
        }
    """
    data = await request.json() or {}
    session_id = data.get("session_id")
    
    if session_id:
        delete_session(session_id)
        return {"message": "Session deleted"}
    
    return {"message": "Logout successful"}


# Token verification route
@app.post("/verify")
async def verify_token(request: Request):
    """
    Verify JWT token validity.
    
    Body:
        {
            "token": "jwt-token"
        }
    """
    from qakeapi import decode_token
    
    data = await request.json()
    token = data.get("token")
    
    if not token:
        return JSONResponse(
            {"error": "Token not provided"},
            status_code=400
        )
    
    try:
        payload = decode_token(token)
        return {
            "valid": True,
            "payload": payload,
        }
    except Exception as e:
        return JSONResponse(
            {
                "valid": False,
                "error": str(e),
            },
            status_code=401
        )


if __name__ == "__main__":
    import asyncio
    import uvicorn
    import sys
    import io
    
    # Fix encoding for Windows console
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 60)
    print("QakeAPI - Authentication and Authorization Example")
    print("=" * 60)
    print("\nFeatures:")
    print("  - JWT tokens (creation and verification)")
    print("  - @require_auth decorator")
    print("  - @require_role decorator")
    print("  - Session management")
    print("\nAvailable users:")
    print("  - admin / admin123 (roles: admin, user)")
    print("  - user / user123 (role: user)")
    print("  - manager / manager123 (roles: manager, user)")
    print("\nUsage examples:")
    print("\n1. Login and get token:")
    print('   curl -X POST http://localhost:8000/login \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"username": "admin", "password": "admin123"}\'')
    print("\n2. Access protected route:")
    print('   curl http://localhost:8000/profile \\')
    print('        -H "Authorization: Bearer <your-token>"')
    print("\n3. Access admin panel:")
    print('   curl http://localhost:8000/admin \\')
    print('        -H "Authorization: Bearer <admin-token>"')
    print("\nDocumentation:")
    print("  http://localhost:8000/docs        - Swagger UI")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
