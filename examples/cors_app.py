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

# Setup CORS configuration
cors_config = {
    "allow_origins": ["http://localhost:3000", "http://127.0.0.1:8001"],
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "allow_credentials": True,
    "expose_headers": ["X-Custom-Header"],
}

@app.router.middleware()
async def cors_middleware(request, handler):
    """CORS middleware implementation"""
    origin = request.headers.get("origin")
    
    if origin and origin in cors_config["allow_origins"]:
        response = await handler(request)
        response.headers.extend([
            (b"Access-Control-Allow-Origin", origin.encode()),
            (b"Access-Control-Allow-Credentials", b"true"),
            (b"Access-Control-Allow-Methods", b", ".join(cors_config["allow_methods"]).encode()),
            (b"Access-Control-Allow-Headers", b", ".join(cors_config["allow_headers"]).encode()),
            (b"Access-Control-Expose-Headers", b", ".join(cors_config["expose_headers"]).encode()),
        ])
        return response
    return await handler(request)

@app.router.route("/", methods=["GET"])
async def index(request: Request):
    """Public endpoint that returns a welcome message"""
    return Response.json({
        "message": "Welcome to the CORS-enabled API!",
        "cors_enabled": True,
        "allowed_origins": cors_config["allow_origins"],
    })

@app.router.route("/api/data", methods=["POST"])
async def create_data(request: Request):
    """Endpoint that accepts POST requests and returns custom headers"""
    data = await request.json()
    response = Response.json({"message": "Data received successfully", "data": data})
    response.headers.append((b"X-Custom-Header", b"custom-value"))
    return response

@app.router.route("/api/data", methods=["OPTIONS"])
async def preflight_data(request: Request):
    """Explicit handler for OPTIONS requests"""
    return Response.json({})

if __name__ == "__main__":
    import uvicorn
    from config import PORTS
    uvicorn.run(app, host="0.0.0.0", port=PORTS['cors_app'])
