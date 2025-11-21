"""
QakeAPI Compression Middleware Example

This example demonstrates how to use compression middleware to reduce response sizes.
"""

from qakeapi import QakeAPI, Request

app = QakeAPI(
    title="Compression Example",
    description="Example of response compression in QakeAPI",
    version="1.0.0",
)

# Add compression middleware
from qakeapi.middleware.compression import CompressionMiddleware

app.add_middleware(
    CompressionMiddleware(
        minimum_size=500,  # Compress responses larger than 500 bytes
        compression_level=6,  # Balance between speed and compression ratio
        skip_paths={"/health"},  # Don't compress health checks
    )
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Compression Example API"}


@app.get("/small")
async def small_response():
    """
    Small response (won't be compressed)

    This response is too small to be compressed.
    """
    return {"message": "This is a small response"}


@app.get("/large")
async def large_response():
    """
    Large response (will be compressed)

    This response is large enough to be compressed automatically.
    """
    # Generate large response
    data = {
        "message": "This is a large response",
        "items": [
            {"id": i, "name": f"Item {i}", "data": "x" * 100} for i in range(100)
        ],
    }
    return data


@app.get("/json")
async def json_response():
    """
    JSON response (will be compressed if large enough)

    JSON responses are automatically compressed if they meet the size threshold.
    """
    return {
        "status": "success",
        "data": {
            "users": [{"id": i, "name": f"User {i}"} for i in range(50)],
            "metadata": {"total": 50, "page": 1},
        },
    }


@app.get("/text")
async def text_response():
    """
    Text response (will be compressed if large enough)

    Text responses can also be compressed.
    """
    from qakeapi.core.responses import PlainTextResponse

    large_text = "This is a large text response. " * 100
    return PlainTextResponse(large_text)


@app.get("/compression-info")
async def compression_info():
    """Get compression information"""
    return {
        "message": "Compression is enabled",
        "minimum_size": 500,
        "supported_algorithms": ["gzip", "deflate"],
        "note": "Check response headers to see if compression was applied",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8005)
