# -*- coding: utf-8 -*-
"""
Performance optimization example with QakeAPI.
"""
import sys
import os
import time
import asyncio
import json
import hashlib
import gzip
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from functools import lru_cache
import aiofiles
import redis.asyncio as redis
from concurrent.futures import ThreadPoolExecutor

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.core.middleware import Middleware
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import BaseModel, Field

# Application initialization
app = Application(title="Performance Optimization Example", version="1.0.3")

# Global variables for caching
memory_cache = {}
cache_timestamps = {}
executor = ThreadPoolExecutor(max_workers=4)

# Pydantic models
class DataProcessRequest(RequestModel):
    data_size: int = Field(..., ge=1, le=1000000, description="Data size for processing")
    complexity: str = Field(..., description="Processing complexity", pattern="^(simple|medium|complex)$")
    use_cache: bool = Field(True, description="Use caching")

class BatchProcessRequest(RequestModel):
    items: List[str] = Field(..., min_items=1, max_items=1000, description="List of items for processing")
    batch_size: int = Field(10, ge=1, le=100, description="Batch size")

# Cache for heavy computations
@lru_cache(maxsize=128)
def heavy_computation(n: int, complexity: str) -> int:
    """
    Heavy computations with caching
    """
    if complexity == "simple":
        return sum(i for i in range(n))
    elif complexity == "medium":
        return sum(i * i for i in range(n))
    else:  # complex
        return sum(i * i * i for i in range(n))

# Async functions for optimization
async def async_data_processing(data: List[int]) -> List[int]:
    """
    Asynchronous data processing
    """
    # Simulate async processing
    await asyncio.sleep(0.1)
    return [x * 2 for x in data]

async def async_file_operation(filename: str, content: str) -> str:
    """
    Asynchronous file operations
    """
    async with aiofiles.open(filename, 'w') as f:
        await f.write(content)
    
    async with aiofiles.open(filename, 'r') as f:
        return await f.read()

async def async_database_query(query: str) -> List[Dict]:
    """
    Asynchronous database query (simulation)
    """
    await asyncio.sleep(0.05)  # Simulate DB delay
    return [{"id": i, "data": f"result_{i}"} for i in range(10)]

def cpu_intensive_task(data: List[int]) -> int:
    """
    CPU-intensive task for execution in a separate thread
    """
    result = 0
    for i in data:
        result += i * i
    return result

# Endpoints

@app.get("/")
async def root(request: Request):
    """
    Basic endpoint
    """
    return {
        "message": "Performance Optimization Example API is running",
        "endpoints": {
            "/data-process": "POST - Data processing with optimization",
            "/batch-process": "POST - Batch processing",
            "/cache-test": "GET - Cache test",
            "/async-operations": "GET - Asynchronous operations",
            "/cpu-intensive": "POST - CPU-intensive tasks",
            "/cache/stats": "GET - Cache statistics",
            "/cache/clear": "POST - Clear cache",
            "/performance/stats": "GET - Performance statistics"
        },
        "optimization_features": [
            "Response caching",
            "Asynchronous processing",
            "Batch processing",
            "Response compression",
            "Performance monitoring",
            "LRU cache for computations"
        ]
    }

@app.post("/data-process")
@validate_request_body(DataProcessRequest)
async def process_data(request: Request):
    """
    Data processing with optimization
    
    This endpoint demonstrates various optimization techniques:
    1. LRU caching for heavy computations
    2. Asynchronous processing
    3. Batch processing
    """
    data = request.validated_data
    
    start_time = time.time()
    
    # Use cached computations
    if data.use_cache:
        computation_result = heavy_computation(data.data_size, data.complexity)
    else:
        # Perform computations without cache
        if data.complexity == "simple":
            computation_result = sum(i for i in range(data.data_size))
        elif data.complexity == "medium":
            computation_result = sum(i * i for i in range(data.data_size))
        else:  # complex
            computation_result = sum(i * i * i for i in range(data.data_size))
    
    # Asynchronous data processing
    data_list = list(range(data.data_size))
    processed_data = await async_data_processing(data_list)
    
    execution_time = time.time() - start_time
    
    return {
        "message": "Data processing completed",
        "data_size": data.data_size,
        "complexity": data.complexity,
        "computation_result": computation_result,
        "processed_items": len(processed_data),
        "execution_time": f"{execution_time:.4f}s",
        "cache_used": data.use_cache
    }

@app.post("/batch-process")
@validate_request_body(BatchProcessRequest)
async def batch_process(request: Request):
    """
    Batch data processing
    
    Demonstrates efficient processing of large data volumes
    using batches and async.
    """
    data = request.validated_data
    
    start_time = time.time()
    results = []
    
    # Process data in batches
    for i in range(0, len(data.items), data.batch_size):
        batch = data.items[i:i + data.batch_size]
        
        # Create tasks for async batch processing
        tasks = []
        for item in batch:
            task = asyncio.create_task(async_data_processing([len(item)]))
            tasks.append(task)
        
        # Run all batch tasks concurrently
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
    
    execution_time = time.time() - start_time
    
    return {
        "message": "Batch processing completed",
        "total_items": len(data.items),
        "batch_size": data.batch_size,
        "batches_processed": len(results),
        "execution_time": f"{execution_time:.4f}s",
        "items_per_second": len(data.items) / execution_time
    }

@app.get("/cache-test")
async def cache_test(request: Request):
    """
    Cache test
    
    The first request will be slow, subsequent ones will be fast due to cache.
    """
    # Simulate heavy operation
    await asyncio.sleep(2)
    
    # Generate data
    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "random_data": [i * i for i in range(1000)],
        "message": "This response is cached for 5 minutes"
    }
    
    return {
        "message": "Cache test response",
        "data": data,
        "cache_info": "This response will be cached for 5 minutes"
    }

@app.get("/async-operations")
async def async_operations(request: Request):
    """
    Demonstration of asynchronous operations
    
    Performs multiple asynchronous operations concurrently.
    """
    start_time = time.time()
    
    # Create multiple asynchronous tasks
    tasks = [
        async_database_query("SELECT * FROM users"),
        async_database_query("SELECT * FROM products"),
        async_file_operation("temp.txt", "Async file operation test"),
        async_data_processing(list(range(100)))
    ]
    
    # Run all tasks concurrently
    results = await asyncio.gather(*tasks)
    
    execution_time = time.time() - start_time
    
    return {
        "message": "Async operations completed",
        "results": {
            "database_queries": len(results[0]) + len(results[1]),
            "file_operation": len(results[2]),
            "data_processing": len(results[3])
        },
        "execution_time": f"{execution_time:.4f}s",
        "parallel_execution": "All operations were executed in parallel"
    }

@app.post("/cpu-intensive")
async def cpu_intensive_operations(request: Request):
    """
    CPU-intensive operations
    
    Demonstrates execution of CPU-intensive tasks in a separate thread
    to prevent blocking the event loop.
    """
    try:
        body = await request.json()
        data_size = body.get("data_size", 10000)
        
        start_time = time.time()
        
        # Create data for processing
        data = list(range(data_size))
        
        # Run CPU-intensive task in a separate thread
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, cpu_intensive_task, data)
        
        execution_time = time.time() - start_time
        
        return {
            "message": "CPU-intensive operation completed",
            "data_size": data_size,
            "result": result,
            "execution_time": f"{execution_time:.4f}s",
            "thread_pool": "Task executed in separate thread"
        }
    except Exception as e:
        return Response.json(
            {"error": "Invalid request data", "details": str(e)},
            status_code=400
        )

@app.get("/cache/stats")
async def cache_stats(request: Request):
    """Cache statistics"""
    # Get middleware
    caching_middleware = None
    for middleware in app.http_router._middleware:
        if hasattr(middleware, '__name__') and middleware.__name__ == "CachingMiddleware":
            caching_middleware = middleware
            break
    
    if not caching_middleware:
        return Response.json({"error": "Caching middleware not found"}, status_code=500)
    
    # Calculate statistics
    total_requests = caching_middleware.cache_stats["hits"] + caching_middleware.cache_stats["misses"]
    hit_rate = (caching_middleware.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
    
    return {
        "message": "Cache statistics",
        "stats": caching_middleware.cache_stats,
        "hit_rate": f"{hit_rate:.2f}%",
        "cache_size": len(memory_cache),
        "cache_ttl": f"{caching_middleware.cache_ttl}s"
    }

@app.post("/cache/clear")
async def clear_cache(request: Request):
    """Clear cache"""
    global memory_cache, cache_timestamps
    
    # Clear cache
    memory_cache.clear()
    cache_timestamps.clear()
    
    # Clear LRU cache
    heavy_computation.cache_clear()
    
    return {
        "message": "Cache cleared successfully",
        "cleared_items": len(memory_cache)
    }

@app.get("/performance/stats")
async def performance_stats(request: Request):
    """Performance statistics"""
    # Get middleware
    performance_middleware = None
    for middleware in app.http_router._middleware:
        if hasattr(middleware, '__name__') and middleware.__name__ == "PerformanceMiddleware":
            performance_middleware = middleware
            break
    
    if not performance_middleware:
        return Response.json({"error": "Performance middleware not found"}, status_code=500)
    
    # Calculate statistics
    if performance_middleware.request_times:
        avg_time = sum(performance_middleware.request_times) / len(performance_middleware.request_times)
        min_time = min(performance_middleware.request_times)
        max_time = max(performance_middleware.request_times)
        
        performance_stats = {
            "total_requests": len(performance_middleware.request_times),
            "avg_response_time": f"{avg_time:.4f}s",
            "min_response_time": f"{min_time:.4f}s",
            "max_response_time": f"{max_time:.4f}s",
            "slow_requests_count": len(performance_middleware.slow_requests)
        }
    else:
        performance_stats = {"total_requests": 0}
    
    return {
        "message": "Performance statistics",
        "performance": performance_stats,
        "slow_requests": performance_middleware.slow_requests[-5:],  # Last 5 slow requests
        "optimization_features": [
            "Response caching",
            "Asynchronous processing",
            "Batch operations",
            "Thread pool for CPU-intensive tasks",
            "Compression middleware"
        ]
    }

@app.get("/optimization/benchmark")
async def optimization_benchmark(request: Request):
    """Optimization benchmark"""
    results = {}
    
    # Test 1: Without caching
    start_time = time.time()
    result1 = heavy_computation(10000, "medium")
    time1 = time.time() - start_time
    results["without_cache"] = {"time": time1, "result": result1}
    
    # Test 2: With caching (second call)
    start_time = time.time()
    result2 = heavy_computation(10000, "medium")
    time2 = time.time() - start_time
    results["with_cache"] = {"time": time2, "result": result2}
    
    # Test 3: Asynchronous processing
    start_time = time.time()
    tasks = [async_data_processing(list(range(100))) for _ in range(10)]
    await asyncio.gather(*tasks)
    time3 = time.time() - start_time
    results["async_processing"] = {"time": time3, "tasks": 10}
    
    # Test 4: Batch processing
    start_time = time.time()
    large_data = list(range(10000))
    batch_size = 100
    for i in range(0, len(large_data), batch_size):
        batch = large_data[i:i + batch_size]
        await async_data_processing(batch)
    time4 = time.time() - start_time
    results["batch_processing"] = {"time": time4, "items": len(large_data)}
    
    return {
        "message": "Optimization benchmark results",
        "results": results,
        "improvements": {
            "cache_speedup": f"{time1/time2:.2f}x" if time2 > 0 else "N/A",
            "async_efficiency": f"{time3:.4f}s for 10 parallel tasks",
            "batch_efficiency": f"{time4:.4f}s for {len(large_data)} items"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8017) 