"""
Example demonstrating logging in QakeAPI.

This example shows how to configure and use the logging system.
"""

import sys
import io
from qakeapi import QakeAPI, CORSMiddleware
from qakeapi.core.logging import configure_logging, get_logger

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configure logging
# Options:
# - level: DEBUG, INFO, WARNING, ERROR, CRITICAL
# - format_type: "text" (human-readable) or "json" (structured)
# - filepath: Optional path to log file (with rotation)
logger = configure_logging(
    level="DEBUG",
    format_type="text",  # or "json" for structured logging
    filepath="app.log",  # Optional: log to file with rotation
)

app = QakeAPI(
    title="Logging Example API",
    version="1.2.0",
    description="Example demonstrating logging",
    debug=True,
)

# Add CORS middleware
app.add_middleware(CORSMiddleware(allow_origins=["*"]))

# Add logging middleware (optional - app has built-in logging)
from qakeapi import LoggingMiddleware
app.add_middleware(LoggingMiddleware())

# Get logger for custom logging
custom_logger = get_logger()


@app.get("/")
def root():
    """Root endpoint."""
    custom_logger.info("Root endpoint accessed", extra={"endpoint": "/"})
    return {"message": "Hello, QakeAPI!"}


@app.get("/users/{id}")
def get_user(id: int):
    """Get user by ID with logging."""
    custom_logger.debug(f"Fetching user {id}", user_id=id)
    
    if id < 0:
        custom_logger.warning(f"Invalid user ID: {id}", user_id=id)
        return {"error": "Invalid ID"}, 400
    
    custom_logger.info(f"User {id} retrieved successfully", user_id=id)
    return {"id": id, "name": f"User {id}"}


@app.post("/users")
async def create_user(request):
    """Create user with logging."""
    data = await request.json()
    custom_logger.info("Creating user", user_data=data)
    
    try:
        # Simulate user creation
        user_id = 1
        custom_logger.info("User created successfully", user_id=user_id, user_data=data)
        return {"id": user_id, "message": "User created"}
    except Exception as e:
        custom_logger.error("Failed to create user", exc_info=True, error=str(e))
        return {"error": "Failed to create user"}, 500


@app.get("/error")
def error_endpoint():
    """Endpoint that raises an error for testing."""
    custom_logger.warning("Error endpoint accessed")
    raise ValueError("This is a test error")


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("QakeAPI Logging Example")
    print("=" * 60)
    print("\nLogging Configuration:")
    print("  Level: DEBUG")
    print("  Format: Text")
    print("  File: app.log (with rotation)")
    print("\nTry these requests:")
    print("  curl http://localhost:8000/")
    print("  curl http://localhost:8000/users/1")
    print("  curl http://localhost:8000/users/-1  # Will log warning")
    print("  curl http://localhost:8000/error     # Will log error")
    print("\nSwagger UI: http://localhost:8000/docs")
    print("=" * 60)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

