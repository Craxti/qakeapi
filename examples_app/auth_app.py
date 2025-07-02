# -*- coding: utf-8 -*-
"""
Authentication example with QakeAPI.
"""
import sys
import os
import hashlib
import secrets
from datetime import datetime, timedelta

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import Field

# Initialize application
app = Application(
    title="Authentication Example",
    version="1.0.3",
    description="Authentication and authorization example with QakeAPI"
)

# Pydantic models
class LoginRequest(RequestModel):
    """Login request model"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class RegisterRequest(RequestModel):
    """Registration request model"""
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")

# In-memory storage
users_db = {}
sessions_db = {}

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

def generate_session_token() -> str:
    """Generate random session token"""
    return secrets.token_urlsafe(32)

def verify_token(token: str) -> dict:
    """Verify session token and return user data"""
    if token in sessions_db:
        session = sessions_db[token]
        if datetime.utcnow() < session["expires_at"]:
            return session["user"]
    return None

@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    return {"message": "Authentication API is running"}

@app.post("/login")
@validate_request_body(LoginRequest)
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
    
    # Generate session token
    token = generate_session_token()
    sessions_db[token] = {
        "user": {
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        },
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@app.post("/register")
@validate_request_body(RegisterRequest)
async def register(request: Request):
    """User registration"""
    register_data = request.validated_data
    
    if register_data.username in users_db:
        return Response.json(
            {"error": "Username already exists"},
            status_code=400
        )
    
    # Create new user
    user = {
        "username": register_data.username,
        "email": register_data.email,
        "password_hash": hash_password(register_data.password),
        "role": "user",
        "created_at": datetime.utcnow()
    }
    
    users_db[register_data.username] = user
    
    return {
        "message": "Registration successful",
        "user": {
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@app.get("/protected")
async def protected_endpoint(request: Request):
    """Protected endpoint requiring authentication"""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response.json(
            {"error": "Authentication required"},
            status_code=401
        )
    
    token = auth_header.split(" ")[1]
    user = verify_token(token)
    
    if not user:
        return Response.json(
            {"error": "Invalid or expired token"},
            status_code=401
        )
    
    return {
        "message": "Access granted to protected resource",
        "user": user
    }

@app.post("/logout")
async def logout(request: Request):
    """User logout"""
    auth_header = request.headers.get("Authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        if token in sessions_db:
            del sessions_db[token]
    
    return {"message": "Logout successful"}

@app.get("/profile")
async def get_profile(request: Request):
    """Get user profile"""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response.json(
            {"error": "Authentication required"},
            status_code=401
        )
    
    token = auth_header.split(" ")[1]
    user = verify_token(token)
    
    if not user:
        return Response.json(
            {"error": "Invalid or expired token"},
            status_code=401
        )
    
    return {
        "profile": user,
        "session_info": {
            "active_sessions": len(sessions_db)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8006) 