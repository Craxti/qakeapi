"""
QakeAPI Monitoring and Metrics Example

This example demonstrates how to use built-in monitoring, metrics, and health checks.
"""

from qakeapi import QakeAPI, Request
from qakeapi.monitoring.health import (
    DiskSpaceHealthCheck,
    HealthChecker,
    HealthCheckMiddleware,
    MemoryHealthCheck,
)
from qakeapi.monitoring.metrics import MetricsCollector, MetricsMiddleware

app = QakeAPI(
    title="Monitoring Example",
    description="Example of monitoring, metrics, and health checks",
    version="1.0.0",
)

# Initialize metrics collector
metrics = MetricsCollector()

# Add metrics middleware
app.add_middleware(MetricsMiddleware(collector=metrics))

# Initialize health checker
health_checker = HealthChecker()

# Add health checks
health_checker.add_check(MemoryHealthCheck())
health_checker.add_check(DiskSpaceHealthCheck(min_free_percent=10.0))

# Add health check middleware
app.add_middleware(HealthCheckMiddleware(health_checker=health_checker))


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Monitoring Example API"}


@app.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    current = metrics.get_current_metrics()
    lifetime = metrics.get_lifetime_metrics()
    return {
        "current": {
            "request_count": current.total_requests,
            "error_count": current.total_errors,
            "average_response_time": current.avg_duration,
            "requests_per_second": current.requests_per_second,
        },
        "lifetime": lifetime,
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    results = await health_checker.check_all()
    overall_status = "healthy" if all(r.is_healthy for r in results) else "unhealthy"

    return {
        "status": overall_status,
        "checks": [
            {
                "name": r.name,
                "status": "healthy" if r.is_healthy else "unhealthy",
                "message": r.message,
            }
            for r in results
        ],
    }


@app.get("/slow")
async def slow_endpoint():
    """Slow endpoint for testing metrics"""
    import asyncio

    await asyncio.sleep(0.5)  # Simulate slow operation
    return {"message": "This was a slow request"}


@app.get("/error")
async def error_endpoint():
    """Error endpoint for testing error metrics"""
    raise ValueError("This is a test error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
