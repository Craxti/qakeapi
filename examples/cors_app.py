import logging

from qakeapi import Application
from qakeapi.core.middleware.cors import CORSConfig, CORSMiddleware
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create application
app = Application(
    title="CORS Example", description="Example application with CORS support"
)

# Setup CORS with custom configuration
cors_config = CORSConfig(
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:8001",
    ],  # Add localhost:8001
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
    expose_headers=["X-Custom-Header"],
    max_age=3600,
)

# Add CORS middleware
app.add_middleware(CORSMiddleware(cors_config))


@app.get("/")
async def index(request: Request) -> Response:
    """Public endpoint that returns a welcome message"""
    return Response.json(
        {
            "message": "Welcome to the CORS-enabled API!",
            "cors_enabled": True,
            "allowed_origins": cors_config.allow_origins,
        }
    )


@app.post("/api/data")
async def create_data(request: Request) -> Response:
    """Endpoint that accepts POST requests and returns custom headers"""
    data = await request.json()

    response = Response.json({"message": "Data received successfully", "data": data})
    response.headers.append((b"X-Custom-Header", b"custom-value"))
    return response


@app.route("/api/data", methods=["OPTIONS"])
async def preflight_data(request: Request) -> Response:
    """Explicit handler for OPTIONS requests"""
    return Response(content={}, status_code=200)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="debug")
