#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance examples application for QakeAPI.
"""
import sys
import os
import time
import asyncio

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application

# Create application
app = Application("Performance Examples")

@app.get("/")
async def home(request):
    """Home page with performance information."""
    return {
        "message": "Performance Examples API",
        "version": "1.0.0",
        "features": [
            "Caching",
            "Profiling",
            "Optimization",
            "Async Operations",
            "Database Optimization"
        ],
        "endpoints": {
            "performance_info": "/performance-info",
            "cache_test": "/cache-test",
            "async_test": "/async-test",
            "benchmark": "/benchmark"
        }
    }

@app.get("/performance-info")
async def performance_info(request):
    """Get performance information."""
    return {
        "caching_enabled": True,
        "async_operations": True,
        "database_optimization": True,
        "response_time": "optimized"
    }

@app.get("/cache-test")
async def cache_test(request):
    """Test caching functionality."""
    # Simulate cache hit
    await asyncio.sleep(0.01)  # Very fast response
    return {
        "message": "Cache test completed",
        "response_time_ms": 10,
        "cache_hit": True
    }

@app.get("/async-test")
async def async_test(request):
    """Test async operations."""
    # Simulate async processing
    await asyncio.sleep(0.1)
    return {
        "message": "Async test completed",
        "response_time_ms": 100,
        "async_operations": True
    }

@app.get("/benchmark")
async def benchmark(request):
    """Run performance benchmark."""
    start_time = time.time()
    
    # Simulate some work
    await asyncio.sleep(0.05)
    
    end_time = time.time()
    response_time = (end_time - start_time) * 1000
    
    return {
        "message": "Benchmark completed",
        "response_time_ms": round(response_time, 2),
        "performance_score": "excellent"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("performance_examples_app:app", host="0.0.0.0", port=8024, reload=False) 