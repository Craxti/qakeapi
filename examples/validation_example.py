"""
Example demonstrating request validation in QakeAPI.

This example shows how to use the built-in validation system
to validate request bodies, query parameters, and path parameters.
"""

import sys
import io
from dataclasses import dataclass
from typing import Optional

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from qakeapi import QakeAPI, CORSMiddleware

app = QakeAPI(
    title="Validation Example API",
    version="1.0.0",
    description="Example demonstrating request validation",
    debug=True,
)

# Add CORS middleware
app.add_middleware(CORSMiddleware(allow_origins=["*"]))


# Define data models using dataclasses
@dataclass
class UserCreate:
    """User creation model with validation."""
    name: str
    age: int
    email: Optional[str] = None


@dataclass
class UserUpdate:
    """User update model."""
    name: Optional[str] = None
    age: Optional[int] = None
    email: Optional[str] = None


# Example 1: Path parameter validation
@app.get("/users/{user_id}")
def get_user(user_id: int):
    """
    Get user by ID.
    
    Path parameter 'user_id' is automatically validated as int.
    """
    return {"user_id": user_id, "name": f"User {user_id}"}


# Example 2: Query parameter validation
@app.get("/search")
def search(q: str, limit: int = 10, offset: int = 0):
    """
    Search endpoint with validated query parameters.
    
    - q: Search query (required, string)
    - limit: Results limit (optional, int, default: 10)
    - offset: Results offset (optional, int, default: 0)
    """
    return {
        "query": q,
        "limit": limit,
        "offset": offset,
        "results": []
    }


# Example 3: Request body validation with dataclass
@app.post("/users")
async def create_user(user: UserCreate):
    """
    Create a new user.
    
    Request body is automatically validated against UserCreate model.
    - name: Required string
    - age: Required integer
    - email: Optional string
    """
    return {
        "message": "User created",
        "user": {
            "name": user.name,
            "age": user.age,
            "email": user.email
        }
    }


# Example 4: PUT request with validation
@app.put("/users/{user_id}")
async def update_user(user_id: int, user: UserUpdate):
    """
    Update user.
    
    Path parameter and request body are both validated.
    """
    return {
        "message": f"User {user_id} updated",
        "updates": {
            "name": user.name,
            "age": user.age,
            "email": user.email
        }
    }


# Example 5: Error handling
@app.post("/validate-test")
async def validate_test(user: UserCreate):
    """
    Test validation errors.
    
    Try sending invalid data to see validation errors:
    - Missing required fields
    - Wrong types
    - Invalid values
    """
    return {
        "message": "Validation passed!",
        "user": {
            "name": user.name,
            "age": user.age,
            "email": user.email
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("QakeAPI Validation Example")
    print("=" * 60)
    print("\nEndpoints:")
    print("  GET  /users/{user_id}     - Path parameter validation")
    print("  GET  /search?q=...        - Query parameter validation")
    print("  POST /users               - Request body validation")
    print("  PUT  /users/{user_id}     - Combined validation")
    print("\nTry these requests:")
    print("  curl -X POST http://localhost:8000/users \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"name\": \"John\", \"age\": 30}'")
    print("\n  curl -X POST http://localhost:8000/users \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"name\": \"John\"}'  # Missing 'age' - will fail")
    print("\n  curl http://localhost:8000/users/abc  # Invalid ID - will fail")
    print("\nSwagger UI: http://localhost:8000/docs")
    print("=" * 60)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

