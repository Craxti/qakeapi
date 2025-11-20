# -*- coding: utf-8 -*-
"""
CSRF protection example with QakeAPI.
"""
import sys
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import Field

# Initialize application
app = Application(
    title="CSRF Protection Example",
    version="1.0.3",
    description="CSRF protection functionality example with QakeAPI"
)

# Token storage (in real application - Redis or database)
csrf_tokens = {}
sessions = {}

# Pydantic models
class LoginRequest(RequestModel):
    """Login request model"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class TransferRequest(RequestModel):
    """Money transfer request model"""
    amount: float = Field(..., gt=0, description="Transfer amount")
    recipient: str = Field(..., description="Recipient username")
    csrf_token: str = Field(..., description="CSRF token")

def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return secrets.token_urlsafe(32)

def generate_session_id() -> str:
    """Generate session ID"""
    return secrets.token_urlsafe(16)

def hash_password(password: str) -> str:
    """Hash password"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_session(username: str) -> str:
    """Create new session"""
    session_id = generate_session_id()
    sessions[session_id] = {
        "username": username,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    return session_id

def get_session(session_id: str) -> Optional[Dict]:
    """Get session by ID"""
    if session_id not in sessions:
        return None
    
    session = sessions[session_id]
    if datetime.utcnow() > session["expires_at"]:
        del sessions[session_id]
        return None
    
    return session

def create_csrf_token(session_id: str) -> str:
    """Create CSRF token for session"""
    token = generate_csrf_token()
    csrf_tokens[session_id] = {
        "token": token,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }
    return token

def validate_csrf_token(session_id: str, token: str) -> bool:
    """Validate CSRF token"""
    if session_id not in csrf_tokens:
        return False
    
    csrf_data = csrf_tokens[session_id]
    if datetime.utcnow() > csrf_data["expires_at"]:
        del csrf_tokens[session_id]
        return False
    
    return csrf_data["token"] == token

def require_auth(func):
    """Decorator for authentication requirement"""
    async def wrapper(request: Request, *args, **kwargs):
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            return Response.json(
                {"error": "Authentication required"},
                status_code=401
            )
        
        session = get_session(session_id)
        if not session:
            return Response.json(
                {"error": "Invalid or expired session"},
                status_code=401
            )
        
        request.session = session
        return await func(request, *args, **kwargs)
    return wrapper

def require_csrf(func):
    """Decorator for CSRF protection"""
    async def wrapper(request: Request, *args, **kwargs):
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            return Response.json(
                {"error": "Session ID required for CSRF protection"},
                status_code=400
            )
        
        # Get CSRF token from request
        if request.method == "POST":
            try:
                data = await request.json()
                csrf_token = data.get("csrf_token")
            except:
                csrf_token = request.headers.get("X-CSRF-Token")
        else:
            csrf_token = request.headers.get("X-CSRF-Token")
        
        if not csrf_token:
            return Response.json(
                {"error": "CSRF token required"},
                status_code=400
            )
        
        if not validate_csrf_token(session_id, csrf_token):
            return Response.json(
                {"error": "Invalid CSRF token"},
                status_code=403
            )
        
        return await func(request, *args, **kwargs)
    return wrapper

# Mock user database
users_db = {
    "admin": {
        "username": "admin",
        "password_hash": hash_password("admin123"),
        "balance": 1000.0
    },
    "user1": {
        "username": "user1", 
        "password_hash": hash_password("password123"),
        "balance": 500.0
    }
}

@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "CSRF Protection API is running",
        "features": [
            "Session-based authentication",
            "CSRF token generation and validation",
            "Protected money transfer operations",
            "Token expiration handling"
        ],
        "endpoints": {
            "/login": "POST - User login",
            "/logout": "POST - User logout",
            "/profile": "GET - User profile (auth required)",
            "/csrf-token": "GET - Get CSRF token (auth required)",
            "/transfer": "POST - Money transfer (CSRF protected)"
        }
    }

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
    
    # Create session
    session_id = create_session(login_data.username)
    
    # Create CSRF token
    csrf_token = create_csrf_token(session_id)
    
    return {
        "message": "Login successful",
        "session_id": session_id,
        "csrf_token": csrf_token,
        "user": {
            "username": user["username"],
            "balance": user["balance"]
        }
    }

@app.post("/logout")
@require_auth
async def logout(request: Request):
    """User logout"""
    session_id = request.headers.get("X-Session-ID")
    
    # Remove session
    if session_id in sessions:
        del sessions[session_id]
    
    # Remove CSRF token
    if session_id in csrf_tokens:
        del csrf_tokens[session_id]
    
    return {"message": "Logout successful"}

@app.get("/profile")
@require_auth
async def get_profile(request: Request):
    """Get user profile"""
    username = request.session["username"]
    user = users_db[username]
    
    return {
        "profile": {
            "username": user["username"],
            "balance": user["balance"],
            "session_created": request.session["created_at"].isoformat()
        }
    }

@app.get("/csrf-token")
@require_auth
async def get_csrf_token(request: Request):
    """Get new CSRF token"""
    session_id = request.headers.get("X-Session-ID")
    csrf_token = create_csrf_token(session_id)
    
    return {
        "csrf_token": csrf_token,
        "expires_at": csrf_tokens[session_id]["expires_at"].isoformat()
    }

@app.post("/transfer")
@require_auth
@require_csrf
@validate_request_body(TransferRequest)
async def transfer_money(request: Request):
    """Transfer money (CSRF protected)"""
    transfer_data = request.validated_data
    username = request.session["username"]
    
    # Check if user exists
    if username not in users_db:
        return Response.json(
            {"error": "User not found"},
            status_code=404
        )
    
    if transfer_data.recipient not in users_db:
        return Response.json(
            {"error": "Recipient not found"},
            status_code=404
        )
    
    # Check balance
    user = users_db[username]
    if user["balance"] < transfer_data.amount:
        return Response.json(
            {"error": "Insufficient balance"},
            status_code=400
        )
    
    # Perform transfer
    user["balance"] -= transfer_data.amount
    users_db[transfer_data.recipient]["balance"] += transfer_data.amount
    
    return {
        "message": "Transfer successful",
        "amount": transfer_data.amount,
        "recipient": transfer_data.recipient,
        "new_balance": user["balance"]
    }

@app.get("/stats")
async def get_stats(request: Request):
    """Get CSRF protection statistics"""
    return {
        "message": "CSRF protection statistics",
        "active_sessions": len(sessions),
        "active_csrf_tokens": len(csrf_tokens),
        "total_users": len(users_db),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "csrf_protection": "active",
        "active_sessions": len(sessions)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8014) 