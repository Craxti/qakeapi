# -*- coding: utf-8 -*-
"""
Rate limiting example with QakeAPI.
"""
import sys
import os
import time
from datetime import datetime
from typing import Dict, List

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response

# Initialize application
app = Application(
    title="Rate Limiting Example",
    version="1.0.3",
    description="Rate limiting functionality example with QakeAPI"
)

# Rate limiting configuration
RATE_LIMITS = {
    "default": {"requests": 10, "window": 60},  # 10 requests per minute
    "strict": {"requests": 5, "window": 60},    # 5 requests per minute
    "burst": {"requests": 20, "window": 60},    # 20 requests per minute
    "api": {"requests": 100, "window": 3600}    # 100 requests per hour
}

# Request tracking storage
request_logs = {}

def check_rate_limit(client_ip: str, limit_type: str = "default") -> bool:
    """Check if request is within rate limits"""
    current_time = time.time()
    limit_config = RATE_LIMITS[limit_type]
    
    # Initialize client log if not exists
    if client_ip not in request_logs:
        request_logs[client_ip] = {}
    
    if limit_type not in request_logs[client_ip]:
        request_logs[client_ip][limit_type] = []
    
    # Clean old requests outside the window
    window_start = current_time - limit_config["window"]
    request_logs[client_ip][limit_type] = [
        req_time for req_time in request_logs[client_ip][limit_type]
        if req_time > window_start
    ]
    
    # Check if limit exceeded
    if len(request_logs[client_ip][limit_type]) >= limit_config["requests"]:
        return False
    
    # Add current request
    request_logs[client_ip][limit_type].append(current_time)
    return True

def get_rate_limit_info(client_ip: str, limit_type: str = "default") -> Dict:
    """Get rate limit information for client"""
    current_time = time.time()
    limit_config = RATE_LIMITS[limit_type]
    
    if client_ip not in request_logs or limit_type not in request_logs[client_ip]:
        return {
            "limit": limit_config["requests"],
            "window": limit_config["window"],
            "remaining": limit_config["requests"],
            "reset_time": current_time + limit_config["window"]
        }
    
    # Clean old requests
    window_start = current_time - limit_config["window"]
    request_logs[client_ip][limit_type] = [
        req_time for req_time in request_logs[client_ip][limit_type]
        if req_time > window_start
    ]
    
    remaining = max(0, limit_config["requests"] - len(request_logs[client_ip][limit_type]))
    
    return {
        "limit": limit_config["requests"],
        "window": limit_config["window"],
        "remaining": remaining,
        "reset_time": current_time + limit_config["window"]
    }

@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    client_ip = request.headers.get("X-Forwarded-For", "127.0.0.1")
    
    return {
        "message": "Rate Limiting API is running",
        "client_ip": client_ip,
        "rate_limits": RATE_LIMITS,
        "endpoints": {
            "/normal": "GET - Normal rate limit (10/min)",
            "/strict": "GET - Strict rate limit (5/min)",
            "/burst": "GET - Burst rate limit (20/min)",
            "/api": "GET - API rate limit (100/hour)",
            "/stats": "GET - Rate limiting statistics"
        }
    }

@app.get("/normal")
async def normal_endpoint(request: Request):
    """Normal rate limited endpoint"""
    client_ip = request.headers.get("X-Forwarded-For", "127.0.0.1")
    
    if not check_rate_limit(client_ip, "default"):
        limit_info = get_rate_limit_info(client_ip, "default")
        return Response.json(
            {
                "error": "Rate limit exceeded",
                "limit_info": limit_info
            },
            status_code=429,
            headers={
                "X-RateLimit-Limit": str(limit_info["limit"]),
                "X-RateLimit-Remaining": str(limit_info["remaining"]),
                "X-RateLimit-Reset": str(int(limit_info["reset_time"]))
            }
        )
    
    limit_info = get_rate_limit_info(client_ip, "default")
    
    return {
        "message": "Normal endpoint accessed successfully",
        "timestamp": datetime.utcnow().isoformat(),
        "rate_limit_info": limit_info
    }

@app.get("/strict")
async def strict_endpoint(request: Request):
    """Strict rate limited endpoint"""
    client_ip = request.headers.get("X-Forwarded-For", "127.0.0.1")
    
    if not check_rate_limit(client_ip, "strict"):
        limit_info = get_rate_limit_info(client_ip, "strict")
        return Response.json(
            {
                "error": "Strict rate limit exceeded",
                "limit_info": limit_info
            },
            status_code=429,
            headers={
                "X-RateLimit-Limit": str(limit_info["limit"]),
                "X-RateLimit-Remaining": str(limit_info["remaining"]),
                "X-RateLimit-Reset": str(int(limit_info["reset_time"]))
            }
        )
    
    limit_info = get_rate_limit_info(client_ip, "strict")
    
    return {
        "message": "Strict endpoint accessed successfully",
        "timestamp": datetime.utcnow().isoformat(),
        "rate_limit_info": limit_info
    }

@app.get("/burst")
async def burst_endpoint(request: Request):
    """Burst rate limited endpoint"""
    client_ip = request.headers.get("X-Forwarded-For", "127.0.0.1")
    
    if not check_rate_limit(client_ip, "burst"):
        limit_info = get_rate_limit_info(client_ip, "burst")
        return Response.json(
            {
                "error": "Burst rate limit exceeded",
                "limit_info": limit_info
            },
            status_code=429,
            headers={
                "X-RateLimit-Limit": str(limit_info["limit"]),
                "X-RateLimit-Remaining": str(limit_info["remaining"]),
                "X-RateLimit-Reset": str(int(limit_info["reset_time"]))
            }
        )
    
    limit_info = get_rate_limit_info(client_ip, "burst")
    
    return {
        "message": "Burst endpoint accessed successfully",
        "timestamp": datetime.utcnow().isoformat(),
        "rate_limit_info": limit_info
    }

@app.get("/api")
async def api_endpoint(request: Request):
    """API rate limited endpoint"""
    client_ip = request.headers.get("X-Forwarded-For", "127.0.0.1")
    
    if not check_rate_limit(client_ip, "api"):
        limit_info = get_rate_limit_info(client_ip, "api")
        return Response.json(
            {
                "error": "API rate limit exceeded",
                "limit_info": limit_info
            },
            status_code=429,
            headers={
                "X-RateLimit-Limit": str(limit_info["limit"]),
                "X-RateLimit-Remaining": str(limit_info["remaining"]),
                "X-RateLimit-Reset": str(int(limit_info["reset_time"]))
            }
        )
    
    limit_info = get_rate_limit_info(client_ip, "api")
    
    return {
        "message": "API endpoint accessed successfully",
        "timestamp": datetime.utcnow().isoformat(),
        "rate_limit_info": limit_info
    }

@app.get("/stats")
async def get_stats(request: Request):
    """Get rate limiting statistics"""
    client_ip = request.headers.get("X-Forwarded-For", "127.0.0.1")
    
    stats = {}
    for limit_type in RATE_LIMITS:
        stats[limit_type] = get_rate_limit_info(client_ip, limit_type)
    
    return {
        "message": "Rate limiting statistics",
        "client_ip": client_ip,
        "timestamp": datetime.utcnow().isoformat(),
        "limits": stats,
        "total_clients": len(request_logs)
    }

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "rate_limiting": "active",
        "total_clients": len(request_logs)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8004) 