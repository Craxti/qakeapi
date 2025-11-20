"""
QakeAPI Rate Limiting Example

This example demonstrates how to use rate limiting to protect your API.
"""

from qakeapi import QakeAPI, Request
from qakeapi.security.rate_limiting import (
    RateLimiter,
    RateLimitRule,
    RateLimitMiddleware,
)

app = QakeAPI(
    title="Rate Limiting Example",
    description="Example of rate limiting in QakeAPI",
    version="1.0.0",
)

# Create rate limiter with rules
rate_limiter = RateLimiter()

# Add rate limit rules
rate_limiter.add_rule(
    "/api/*",
    RateLimitRule(
        requests=10,  # 10 requests
        window=60,  # per 60 seconds
    ),
)

rate_limiter.add_rule(
    "/api/premium/*",
    RateLimitRule(
        requests=100,  # 100 requests
        window=60,  # per 60 seconds
    ),
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware(
        rate_limiter=rate_limiter,
        skip_paths={"/", "/health", "/docs", "/redoc"},
    )
)


@app.get("/")
async def root():
    """Root endpoint (not rate limited)"""
    return {"message": "Rate Limiting Example API"}


@app.get("/api/public")
async def public_endpoint():
    """
    Public API endpoint (rate limited: 10 requests per minute)

    Try making more than 10 requests in a minute to see rate limiting in action.
    """
    return {
        "message": "This is a public endpoint",
        "rate_limit": "10 requests per minute",
    }


@app.get("/api/premium/data")
async def premium_endpoint():
    """
    Premium API endpoint (rate limited: 100 requests per minute)

    This endpoint has a higher rate limit for premium users.
    """
    return {
        "message": "This is a premium endpoint",
        "rate_limit": "100 requests per minute",
        "data": {"premium": True, "features": ["advanced", "priority"]},
    }


@app.get("/api/stats")
async def rate_limit_stats():
    """Get rate limiting statistics"""
    stats = rate_limiter.get_stats()
    return {
        "total_requests": stats.get("total_requests", 0),
        "blocked_requests": stats.get("blocked_requests", 0),
        "active_limits": len(rate_limiter.rules),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
