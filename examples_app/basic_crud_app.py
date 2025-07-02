# -*- coding: utf-8 -*-
"""
Basic CRUD example with QakeAPI.
"""
import sys
import os
from typing import Dict, List, Optional

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import Field

# Initialize application
app = Application(
    title="Basic CRUD Example",
    version="1.0.3",
    description="Basic CRUD operations example with QakeAPI"
)

# Pydantic models
class UserCreate(RequestModel):
    """User creation model"""
    username: str = Field(..., description="Username")
    email: str = Field(..., description="User email")
    password: str = Field(..., description="Password")

class UserUpdate(RequestModel):
    """User update model"""
    username: Optional[str] = Field(None, description="New username")
    email: Optional[str] = Field(None, description="New email")

# In-memory database
users_db = {}
next_user_id = 1

@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    return {"message": "Basic CRUD API is running"}

@app.post("/users", status_code=201)
@validate_request_body(UserCreate)
async def create_user(request: Request):
    """Create new user"""
    global next_user_id
    user_data = request.validated_data
    
    user = {
        "id": next_user_id,
        "username": user_data.username,
        "email": user_data.email
    }
    
    users_db[next_user_id] = user
    next_user_id += 1
    
    return user

@app.get("/users")
async def list_users(request: Request):
    """Get all users"""
    return list(users_db.values())

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

@app.put("/users/{user_id}")
@validate_request_body(UserUpdate)
async def update_user(request: Request):
    user_id = int(request.path_params.get("user_id"))
    """Update user"""
    if user_id not in users_db:
        return Response.json(
            {"error": "User not found"},
            status_code=404
        )
    
    user_data = request.validated_data
    user = users_db[user_id]
    
    if user_data.username is not None:
        user["username"] = user_data.username
    if user_data.email is not None:
        user["email"] = user_data.email
    
    return user

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(request: Request):
    user_id = int(request.path_params.get("user_id"))
    """Delete user"""
    if user_id not in users_db:
        return Response.json(
            {"error": "User not found"},
            status_code=404
        )
    
    del users_db[user_id]
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001) 