"""
Example demonstrating rate limiting in QakeAPI.

This example shows how to use the @rate_limit decorator
to protect routes from excessive requests.
"""

import sys
import io
from qakeapi import QakeAPI, CORSMiddleware, rate_limit

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = QakeAPI(
    title="Rate Limit Example API",
    version="1.0.0",
    description="Example demonstrating rate limiting",
    debug=True,
)

# Add CORS middleware
app.add_middleware(CORSMiddleware(allow_origins=["*"]))


# Example 1: Basic rate limiting (10 requests per minute)
@rate_limit(requests_per_minute=10, window_seconds=60)
@app.get("/limited")
def limited_endpoint():
    """Endpoint with rate limiting - 10 requests per minute."""
    return {
        "message": "This endpoint is rate limited",
        "limit": "10 requests per minute"
    }


# Example 2: Strict rate limiting (5 requests per minute)
@rate_limit(requests_per_minute=5, window_seconds=60)
@app.get("/strict")
def strict_endpoint():
    """Endpoint with strict rate limiting - 5 requests per minute."""
    return {
        "message": "This endpoint has strict rate limiting",
        "limit": "5 requests per minute"
    }


# Example 3: Rate limiting with custom window (20 requests per 30 seconds)
@rate_limit(requests_per_minute=20, window_seconds=30)
@app.post("/upload")
async def upload_endpoint(request):
    """Upload endpoint with custom time window."""
    data = await request.json()
    return {
        "message": "Upload endpoint",
        "limit": "20 requests per 30 seconds",
        "received": data
    }


# Example 4: No rate limiting (unlimited)
@app.get("/unlimited")
def unlimited_endpoint():
    """Endpoint without rate limiting."""
    return {
        "message": "This endpoint has no rate limiting"
    }


# Example 5: Custom rate limit key (per user)
@rate_limit(
    requests_per_minute=3,
    key_func=lambda req: f"user:{req.headers.get('user-id', 'anonymous')}"
)
@app.get("/user-specific")
def user_specific_endpoint():
    """Rate limit per user ID from header."""
    return {
        "message": "Rate limited per user",
        "limit": "3 requests per minute per user"
    }


# Example 6: Different limits for different endpoints
@rate_limit(requests_per_minute=100, window_seconds=60)
@app.get("/public")
def public_endpoint():
    """Public endpoint with higher limit."""
    return {"message": "Public endpoint", "limit": "100/min"}


@rate_limit(requests_per_minute=10, window_seconds=60)
@app.get("/api/data")
def api_data():
    """API endpoint with lower limit."""
    return {"message": "API data", "limit": "10/min"}


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("QakeAPI Rate Limiting Example")
    print("=" * 60)
    print("\nEndpoints:")
    print("  GET  /limited        - 10 requests/minute")
    print("  GET  /strict         - 5 requests/minute")
    print("  POST /upload         - 20 requests/30 seconds")
    print("  GET  /unlimited      - No rate limit")
    print("  GET  /user-specific  - 3 requests/minute per user")
    print("  GET  /public         - 100 requests/minute")
    print("  GET  /api/data       - 10 requests/minute")
    print("\nTry these requests:")
    print("  # Make 11 requests quickly to /limited to see rate limit")
    print("  for i in {1..11}; do curl http://localhost:8000/limited; done")
    print("\n  # Check rate limit headers")
    print("  curl -v http://localhost:8000/limited")
    print("\nSwagger UI: http://localhost:8000/docs")
    print("=" * 60)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

