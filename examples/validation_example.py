"""
Validation example.

Demonstrates:
- Using BaseModel for request validation
- Field validation
- Automatic validation errors
"""

from qakeapi import QakeAPI, Request, HTTPException
from qakeapi import JSONResponse
from qakeapi.validation import (
    BaseModel,
    Field,
    ValidationError,
    StringValidator,
    IntegerValidator,
    EmailValidator,
)


app = QakeAPI(title="Validation Example")


class UserCreate(BaseModel):
    """User creation model."""

    name: str = Field(validator=StringValidator(min_length=3, max_length=50))
    email: str = Field(validator=EmailValidator())  # Use EmailValidator for email
    age: int = Field(validator=IntegerValidator(min_value=18, max_value=120))


class UserUpdate(BaseModel):
    """User update model."""

    name: str = Field(
        validator=StringValidator(min_length=3, max_length=50),
        required=False,
    )
    email: str = Field(
        validator=EmailValidator(),
        required=False,
    )
    age: int = Field(
        validator=IntegerValidator(min_value=18, max_value=120),
        required=False,
    )


@app.post("/users")
async def create_user(user: UserCreate):
    """Create user with validation."""
    return {
        "message": "User created",
        "user": {
            "name": user.name,
            "email": user.email,
            "age": user.age,
        },
    }


@app.put("/users/{user_id}")
async def update_user(user_id: int, user: UserUpdate):
    """Update user with partial validation."""
    return {
        "message": "User updated",
        "user_id": user_id,
        "updates": user.dict(exclude_none=True),
    }


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    return JSONResponse(
        {"detail": str(exc), "errors": exc.errors},
        status_code=422,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
