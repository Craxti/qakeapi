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
    
    if request.method == "OPTIONS":
        response = Response.json({})
        if origin and origin in cors_config["allow_origins"]:
            response.headers = [
                (b"Access-Control-Allow-Origin", origin.encode()),
                (b"Access-Control-Allow-Credentials", b"true"),
                (b"Access-Control-Allow-Methods", b", ".join(method.encode() for method in cors_config["allow_methods"])),
                (b"Access-Control-Allow-Headers", b", ".join(header.encode() for header in cors_config["allow_headers"])),
                (b"Access-Control-Max-Age", b"3600"),
            ]
        return response
    
    response = await handler(request)
    if origin and origin in cors_config["allow_origins"]:
        if not hasattr(response, "headers"):
            response.headers = []
        elif response.headers is None:
            response.headers = []
        response.headers.extend([
            (b"Access-Control-Allow-Origin", origin.encode()),
            (b"Access-Control-Allow-Credentials", b"true"),
            (b"Access-Control-Expose-Headers", b", ".join(header.encode() for header in cors_config["expose_headers"])),
        ])
    return response

@app.router.route("/", methods=["GET"])
async def index(request: Request):
    """Public endpoint that returns a welcome message"""
    return Response.json({
        "message": "Welcome to the CORS-enabled API!",
        "cors_enabled": True,
        "allowed_origins": cors_config["allow_origins"],
    })

@app.router.route("/api/data", methods=["GET", "POST"])
async def handle_data(request: Request):
    """Endpoint that handles both GET and POST requests"""
    if request.method == "GET":
        return Response.json({
            "message": "API data endpoint",
            "supported_methods": ["GET", "POST"]
        })
    elif request.method == "POST":
        data = await request.json()
        response = Response.json({"message": "Data received successfully", "data": data})
        response.headers.append((b"X-Custom-Header", b"custom-value"))
        return response

if __name__ == "__main__":
    import uvicorn
    from config import PORTS
    uvicorn.run(app, host="0.0.0.0", port=PORTS['cors_app'])
