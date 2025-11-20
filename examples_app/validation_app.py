# -*- coding: utf-8 -*-
"""
Request validation example with QakeAPI.
"""
import sys
import os
import re
from datetime import datetime
from typing import Optional

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import Field, validator, EmailStr

# Initialize application
app = Application(
    title="Validation Example",
    version="1.0.3",
    description="Request validation example with QakeAPI"
)

# Pydantic models with custom validators
class UserCreate(RequestModel):
    """User creation model with validation"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    age: Optional[int] = Field(None, ge=0, le=150, description="Age")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

class SearchRequest(RequestModel):
    """Search request model"""
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Result limit")
    offset: Optional[int] = Field(0, ge=0, description="Result offset")

# In-memory database
users_db = {}
next_user_id = 1

@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "Validation API is running",
        "features": [
            "Custom field validation",
            "Password strength validation",
            "Username format validation",
            "Email validation",
            "Search parameter validation"
        ]
    }

@app.post("/users")
@validate_request_body(UserCreate)
async def create_user(request: Request):
    """Create new user with validation"""
    global next_user_id
    user_data = request.validated_data
    
    # Check if username already exists
    if any(u["username"] == user_data.username for u in users_db.values()):
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
        "id": next_user_id,
        "username": user_data.username,
        "email": user_data.email,
        "age": user_data.age,
        "created_at": datetime.utcnow().isoformat()
    }
    
    users_db[next_user_id] = user
    next_user_id += 1
    
    return {
        "message": "User created successfully",
        "user": user
    }

@app.get("/users/{user_id}")
async def get_user(request: Request):
    """Get user by ID"""
    user_id = int(request.path_params.get("user_id"))
    if user_id not in users_db:
        return Response.json(
            {"error": "User not found"},
            status_code=404
        )
    return users_db[user_id]

@app.get("/search")
async def search_users(request: Request):
    """Search users with validation"""
    try:
        # Parse and validate query parameters
        query = request.query_params.get("query", "")
        limit = int(request.query_params.get("limit", "10"))
        offset = int(request.query_params.get("offset", "0"))
        
        # Validate parameters
        if not query:
            return Response.json(
                {"error": "Query parameter is required"},
                status_code=400
            )
        
        if limit < 1 or limit > 100:
            return Response.json(
                {"error": "Limit must be between 1 and 100"},
                status_code=400
            )
        
        if offset < 0:
            return Response.json(
                {"error": "Offset must be non-negative"},
                status_code=400
            )
        
        # Perform search
        results = []
        for user in users_db.values():
            if (query.lower() in user["username"].lower() or 
                query.lower() in user["email"].lower()):
                results.append(user)
        
        # Apply pagination
        start = offset
        end = start + limit
        paginated_results = results[start:end]
        
        return {
            "query": query,
            "total": len(results),
            "limit": limit,
            "offset": offset,
            "results": paginated_results
        }
        
    except ValueError as e:
        return Response.json(
            {"error": f"Invalid parameter: {str(e)}"},
            status_code=400
        )

@app.get("/validation-rules")
async def get_validation_rules(request: Request):
    """Get validation rules documentation"""
    return {
        "username": {
            "min_length": 3,
            "max_length": 50,
            "pattern": "Only letters, numbers, and underscores allowed"
        },
        "email": {
            "format": "Valid email address required"
        },
        "password": {
            "min_length": 8,
            "requirements": [
                "At least one uppercase letter",
                "At least one lowercase letter",
                "At least one digit"
            ]
        },
        "age": {
            "min_value": 0,
            "max_value": 150,
            "optional": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8008) 