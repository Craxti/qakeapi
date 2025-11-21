# -*- coding: utf-8 -*-
"""
Middleware example with QakeAPI.
"""
import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, Any

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.core.middleware import Middleware

# Initialize application
app = Application(
    title="Middleware Example",
    version="1.0.3",
    description="Middleware functionality example with QakeAPI"
)

# Middleware classes will be defined as decorators below

# Add middleware to application using decorators
@app.middleware()
class LoggingMiddleware:
    """Logging middleware for request/response logging"""
    
    def __init__(self):
        self.request_count = 0
    
    async def process_request(self, request: Request) -> None:
        """Process incoming request"""
        self.request_count += 1
        request.start_time = time.time()
        
        print(f"[{datetime.now().isoformat()}] Request #{self.request_count}")
        print(f"  Method: {request.method}")
        print(f"  Path: {request.path}")
        print(f"  Headers: {dict(request.headers)}")
    
    async def process_response(self, request: Request, response: Response) -> Response:
        """Process outgoing response"""
        duration = time.time() - request.start_time
        
        print(f"[{datetime.now().isoformat()}] Response")
        print(f"  Status: {response.status_code}")
        print(f"  Duration: {duration:.3f}s")
        print(f"  Headers: {dict(response.headers)}")
        
        # Add custom header
        response.headers["X-Request-Duration"] = f"{duration:.3f}s"
        response.headers["X-Request-Count"] = str(self.request_count)
        
        return response

@app.middleware()
class AuthenticationMiddleware:
    """Authentication middleware"""
    
    def __init__(self):
        self.public_paths = {"/", "/public", "/health"}
    
    async def process_request(self, request: Request) -> None:
        """Check authentication for protected routes"""
        if request.path in self.public_paths:
            return
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise Response.json(
                {"error": "Authentication required"},
                status_code=401
            )
        
        # Simple token validation (in real app, validate JWT)
        token = auth_header.split(" ")[1]
        if token != "valid-token":
            raise Response.json(
                {"error": "Invalid token"},
                status_code=401
            )
        
        # Add user info to request
        request.user = {"id": 1, "username": "testuser"}

@app.middleware()
class RateLimitMiddleware:
    """Rate limiting middleware"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    async def process_request(self, request: Request) -> None:
        """Check rate limits"""
        client_ip = request.headers.get("X-Forwarded-For", "127.0.0.1")
        current_time = time.time()
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < 60
            ]
        else:
            self.requests[client_ip] = []
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise Response.json(
                {"error": "Rate limit exceeded"},
                status_code=429
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)

@app.middleware()
class CachingMiddleware:
    """Caching middleware"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def process_request(self, request: Request) -> None:
        """Check cache for GET requests"""
        if request.method != "GET":
            return
        
        cache_key = f"{request.method}:{request.path}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                # Return cached response
                raise Response.json(cached_data, headers={"X-Cache": "HIT"})
    
    async def process_response(self, request: Request, response: Response) -> Response:
        """Cache GET responses"""
        if request.method == "GET" and response.status_code == 200:
            try:
                cache_key = f"{request.method}:{request.path}"
                response_data = json.loads(response.body.decode())
                self.cache[cache_key] = (response_data, time.time())
                response.headers["X-Cache"] = "MISS"
            except:
                pass
        
        return response

# Routes
@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "Middleware API is running",
        "middleware": [
            "LoggingMiddleware - Request/response logging",
            "AuthenticationMiddleware - Token-based auth",
            "RateLimitMiddleware - Rate limiting",
            "CachingMiddleware - Response caching"
        ],
        "endpoints": {
            "/public": "Public endpoint (no auth required)",
            "/protected": "Protected endpoint (auth required)",
            "/health": "Health check endpoint"
        }
    }

@app.get("/public")
async def public_endpoint(request: Request):
    """Public endpoint - no authentication required"""
    return {
        "message": "This is a public endpoint",
        "timestamp": datetime.utcnow().isoformat(),
        "user": "anonymous"
    }

@app.get("/protected")
async def protected_endpoint(request: Request):
    """Protected endpoint - authentication required"""
    return {
        "message": "This is a protected endpoint",
        "timestamp": datetime.utcnow().isoformat(),
        "user": request.user
    }

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "middleware_status": {
            "logging": "active",
            "authentication": "active", 
            "rate_limiting": "active",
            "caching": "active"
        }
    }

@app.get("/cache-test")
async def cache_test(request: Request):
    """Test caching middleware"""
    return {
        "message": "This response should be cached",
        "timestamp": datetime.utcnow().isoformat(),
        "cache_info": "First request will be cached, subsequent requests will be served from cache"
    }

@app.post("/clear-cache")
async def clear_cache(request: Request):
    """Clear cache (admin only)"""
    # Get caching middleware
    for middleware in app.middleware:
        if isinstance(middleware, CachingMiddleware):
            middleware.cache.clear()
            return {"message": "Cache cleared successfully"}
    
    return {"message": "Caching middleware not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8010) 