# -*- coding: utf-8 -*-
"""
JWT authentication example with QakeAPI.
"""
import sys
import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import Field, EmailStr

# Initialize application
app = Application(
    title="JWT Authentication Example",
    version="1.0.3",
    description="JWT authentication example with QakeAPI"
)

# JWT configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 3600  # 1 hour

# Pydantic models
class UserRegister(RequestModel):
    """User registration model"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")

class UserLogin(RequestModel):
    """User login model"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class TokenRefresh(RequestModel):
    """Token refresh model"""
    refresh_token: str = Field(..., description="Refresh token")

# In-memory storage
users_db = {}
refresh_tokens_db = {}

# Default admin user
users_db["admin"] = {
    "username": "admin",
    "email": "admin@example.com",
    "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
    "role": "admin",
    "created_at": datetime.utcnow()
}

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_tokens(user_data: dict) -> tuple:
    """Create access and refresh tokens"""
    # Access token payload
    access_payload = {
        "user_id": user_data["username"],
        "email": user_data["email"],
        "role": user_data["role"],
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION),
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    # Refresh token payload
    refresh_payload = {
        "user_id": user_data["username"],
        "exp": datetime.utcnow() + timedelta(days=30),
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    
    # Generate tokens
    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return access_token, refresh_token

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(roles: list = None):
    """Decorator for authentication requirement"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            auth_header = request.headers.get("Authorization")
            
            if not auth_header or not auth_header.startswith("Bearer "):
                return Response.json(
                    {"error": "Authentication required"},
                    status_code=401
                )
            
            token = auth_header.split(" ")[1]
            payload = verify_token(token)
            
            if not payload:
                return Response.json(
                    {"error": "Invalid or expired token"},
                    status_code=401
                )
            
            if payload.get("type") != "access":
                return Response.json(
                    {"error": "Invalid token type"},
                    status_code=401
                )
            
            # Check roles if specified
            if roles and payload.get("role") not in roles:
                return Response.json(
                    {"error": "Insufficient permissions"},
                    status_code=403
                )
            
            # Add user info to request
            request.user = payload
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "JWT Authentication API is running",
        "endpoints": {
            "/register": "POST - User registration",
            "/login": "POST - User login",
            "/refresh": "POST - Token refresh",
            "/public": "GET - Public endpoint",
            "/protected": "GET - Protected endpoint (auth required)",
            "/admin": "GET - Admin endpoint (admin role required)"
        }
    }

@app.post("/register")
@validate_request_body(UserRegister)
async def register(request: Request):
    """User registration"""
    user_data = request.validated_data
    
    # Check if username already exists
    if user_data.username in users_db:
        return Response.json(
            {"error": "Username already exists"},
            status_code=400
        )
    
    # Check if email already exists
    if any(u["email"] == user_data.email for u in users_db.values()):
        return Response.json(
            {"error": "Email already exists"},
            status_code=400
        )
    
    # Create user
    user = {
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "role": "user",
        "created_at": datetime.utcnow()
    }
    
    users_db[user_data.username] = user
    
    return {
        "message": "User registered successfully",
        "user": {
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@app.post("/login")
@validate_request_body(UserLogin)
async def login(request: Request):
    """User login"""
    login_data = request.validated_data
    
    if login_data.username not in users_db:
        return Response.json(
            {"error": "Invalid credentials"},
            status_code=401
        )
    
    user = users_db[login_data.username]
    if user["password_hash"] != hash_password(login_data.password):
        return Response.json(
            {"error": "Invalid credentials"},
            status_code=401
        )
    
    # Create tokens
    access_token, refresh_token = create_tokens(user)
    
    # Store refresh token
    refresh_tokens_db[refresh_token] = {
        "user_id": user["username"],
        "created_at": datetime.utcnow()
    }
    
    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": JWT_EXPIRATION,
        "user": {
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@app.post("/refresh")
@validate_request_body(TokenRefresh)
async def refresh_token(request: Request):
    """Refresh access token"""
    refresh_data = request.validated_data
    refresh_token = refresh_data.refresh_token
    
    # Verify refresh token
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return Response.json(
            {"error": "Invalid refresh token"},
            status_code=401
        )
    
    # Check if refresh token exists in database
    if refresh_token not in refresh_tokens_db:
        return Response.json(
            {"error": "Refresh token not found"},
            status_code=401
        )
    
    user_id = payload.get("user_id")
    if user_id not in users_db:
        return Response.json(
            {"error": "User not found"},
            status_code=401
        )
    
    user = users_db[user_id]
    
    # Create new tokens
    new_access_token, new_refresh_token = create_tokens(user)
    
    # Remove old refresh token and store new one
    del refresh_tokens_db[refresh_token]
    refresh_tokens_db[new_refresh_token] = {
        "user_id": user["username"],
        "created_at": datetime.utcnow()
    }
    
    return {
        "message": "Token refreshed successfully",
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "expires_in": JWT_EXPIRATION
    }

@app.get("/public")
async def public_endpoint(request: Request):
    """Public endpoint - no authentication required"""
    return {
        "message": "This is a public endpoint",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/protected")
@require_auth()
async def protected_endpoint(request: Request):
    """Protected endpoint - authentication required"""
    return {
        "message": "This is a protected endpoint",
        "user": request.user,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/admin")
@require_auth(roles=["admin"])
async def admin_endpoint(request: Request):
    """Admin endpoint - admin role required"""
    return {
        "message": "This is an admin endpoint",
        "user": request.user,
        "admin_data": {
            "total_users": len(users_db),
            "active_refresh_tokens": len(refresh_tokens_db),
            "server_time": datetime.utcnow().isoformat()
        }
    }

@app.post("/logout")
@require_auth()
async def logout(request: Request):
    """User logout"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        # In a real app, you might want to blacklist the token
        # For now, we'll just return success
    
    return {"message": "Logout successful"}

@app.get("/profile")
@require_auth()
async def get_profile(request: Request):
    """Get user profile"""
    user_id = request.user.get("user_id")
    if user_id in users_db:
        user = users_db[user_id]
        return {
            "profile": {
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "created_at": user["created_at"].isoformat()
            }
        }
    
    return Response.json(
        {"error": "User not found"},
        status_code=404
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8009) 