import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Awaitable

from qakeapi.core.application import Application
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response, JSONResponse
from qakeapi.core.middleware import Middleware

from config import PORTS

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='rate_limit.log'
)
logger = logging.getLogger(__name__)

# Configuration
REQUESTS_PER_MINUTE = 5
WINDOW_SIZE = 60  # seconds
RATE_LIMIT_PORT = 8007  # Используем фиксированный порт

class RateLimitMiddleware(Middleware):
    def __init__(self):
        self.request_history: Dict[str, List[datetime]] = {}
        self.requests_per_minute = REQUESTS_PER_MINUTE

    async def __call__(self, request: Request, handler: Callable) -> Response:
        return await self.process_request(request, handler)

    async def process_request(self, request: Request, handler: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        
        # Initialize history for new clients
        if client_ip not in self.request_history:
            self.request_history[client_ip] = []
        
        # Clean old requests
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        self.request_history[client_ip] = [
            ts for ts in self.request_history[client_ip] 
            if ts > minute_ago
        ]
        
        # Check rate limit
        if len(self.request_history[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                content={"detail": "Rate limit exceeded"},
                status_code=429
            )
        
        # Add current request timestamp
        self.request_history[client_ip].append(now)
        
        # Process request
        return await handler(request)

# Create application
app = Application()

# Add rate limit middleware
middleware = RateLimitMiddleware()
app.add_middleware(middleware)

@app.get("/")
async def index(request: Request) -> Response:
    return JSONResponse(
        content={"message": "Rate limit example server is running"},
        status_code=200
    )

@app.get("/status")
async def status(request: Request) -> Response:
    client_ip = request.client.host if request.client else "unknown"
    requests_count = len(middleware.request_history.get(client_ip, []))
    return JSONResponse(
        content={
            "requests_count": requests_count,
            "requests_remaining": middleware.requests_per_minute - requests_count
        },
        status_code=200
    )

if __name__ == "__main__":
    import uvicorn
    print("Starting rate limit example server...")
    uvicorn.run(app, host="0.0.0.0", port=RATE_LIMIT_PORT) 