"""
QakeAPI Error Handling Example

This example demonstrates comprehensive error handling in QakeAPI.
"""

from qakeapi import QakeAPI, Request, JSONResponse
from qakeapi.core.exceptions import (
    HTTPException,
    ValidationException,
    NotFoundException,
    AuthenticationException,
)
from qakeapi.core.error_handling import ErrorHandler
from qakeapi.utils.status import status

app = QakeAPI(
    title="Error Handling Example",
    description="Example of error handling in QakeAPI",
    version="1.0.0",
    debug=True,  # Enable debug mode for detailed error messages
)

# Create error handler
error_handler = ErrorHandler(debug=True)


# Register custom exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.path),
        },
    )


@app.exception_handler(ValidationException)
async def validation_error_handler(request: Request, exc: ValidationException):
    """Custom validation error handler"""
    # ValidationException has status_code=422 by default, but we override to 400
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Error",
            "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
            "details": getattr(exc, "errors", None) or [],
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler"""
    return await error_handler.handle_exception(request, exc)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Error Handling Example API"}


@app.get("/success")
async def success():
    """Successful endpoint"""
    return {"status": "success", "message": "Everything works fine!"}


@app.get("/not-found")
async def not_found():
    """Raise 404 error"""
    raise NotFoundException("Resource not found")


@app.get("/validation-error")
async def validation_error():
    """Raise validation error"""
    # ValidationException has status_code=422 by default
    # Our custom handler will override it to 400
    raise ValidationException("Invalid input data")


@app.get("/auth-error")
async def auth_error():
    """Raise authentication error"""
    raise AuthenticationException("Authentication required")


@app.get("/http-error/{code}")
async def http_error(code: int):
    """Raise HTTP error with custom status code"""
    if code < 400 or code >= 600:
        raise HTTPException(400, "Status code must be between 400 and 599")
    raise HTTPException(code, f"HTTP {code} error")


@app.get("/generic-error")
async def generic_error():
    """Raise generic Python exception"""
    raise ValueError("This is a generic Python error")


@app.post("/validate")
async def validate_data(request: Request):
    """Validate request data"""
    data = await request.json()

    # Simple validation
    if "name" not in data:
        raise ValidationException("Name is required", errors=["name field is missing"])

    if "email" not in data:
        raise ValidationException(
            "Email is required", errors=["email field is missing"]
        )

    # Email validation
    if "@" not in data.get("email", ""):
        raise ValidationException(
            "Invalid email format", errors=["email must contain @"]
        )

    return {"status": "valid", "data": data}


@app.get("/error-chain")
async def error_chain():
    """Demonstrate error chaining"""
    try:
        # Simulate nested error
        try:
            raise ValueError("Inner error")
        except ValueError as e:
            raise RuntimeError("Outer error") from e
    except RuntimeError as e:
        raise HTTPException(500, "Chained error occurred") from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)
