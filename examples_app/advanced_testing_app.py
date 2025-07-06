#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Testing Example Application - Simplified Version

This application demonstrates advanced testing capabilities of QakeAPI.
"""

import asyncio
import time
import random
from qakeapi import Application

# Create application
app = Application("Advanced Testing Example")

# Routes for testing different scenarios
@app.get("/")
async def home(request):
    """Home page with testing information."""
    return {
        "message": "Advanced Testing API",
        "version": "1.0.3",
        "features": [
            "Property-based testing",
            "Chaos engineering",
            "Concurrent testing",
            "Performance testing",
            "Memory leak detection",
            "Test data factories",
            "Test environment management",
            "Advanced test reporting"
        ],
        "endpoints": {
            "users": "/users",
            "products": "/products", 
            "orders": "/orders",
            "performance": "/performance",
            "chaos": "/chaos",
            "concurrent": "/concurrent",
            "memory": "/memory",
            "test-report": "/test-report"
        }
    }

@app.get("/users")
async def get_users(request):
    """Get all users - for property-based testing."""
    return {"users": []}

@app.post("/users")
async def create_user(request):
    """Create a user - for mutation testing."""
    try:
        user_data = await request.json()
        return {
            "id": 1,
            "name": user_data.get("name", "test"),
            "email": user_data.get("email", "test@example.com")
        }
    except:
        return {"error": "No user data provided"}

@app.get("/products")
async def get_products(request):
    """Get all products - for chaos engineering tests."""
    return {"products": []}

@app.post("/products")
async def create_product(request):
    """Create a product - for performance testing."""
    try:
        product_data = await request.json()
        return {
            "id": 1,
            "name": product_data.get("name", "test"),
            "price": product_data.get("price", 0.0),
            "category": product_data.get("category", "test")
        }
    except:
        return {"error": "No product data provided"}

@app.get("/orders")
async def get_orders(request):
    """Get all orders - for concurrent testing."""
    return {"orders": []}

@app.post("/orders")
async def create_order(request):
    """Create an order - for memory leak detection."""
    try:
        order_data = await request.json()
        return {
            "id": 1,
            "user_id": order_data.get("user_id", 1),
            "product_id": order_data.get("product_id", 1),
            "quantity": order_data.get("quantity", 1),
            "total": order_data.get("total", 0.0),
            "created_at": time.time()
        }
    except:
        return {"error": "No order data provided"}

@app.get("/performance")
async def performance_test(request):
    """Performance test endpoint."""
    # Simulate some processing
    await asyncio.sleep(0.1)
    
    # Generate some data
    data = []
    for i in range(100):
        data.append({
            "id": i,
            "value": i * 2,
            "timestamp": time.time()
        })
    
    return {"data": data, "count": len(data)}

@app.get("/chaos")
async def chaos_test(request):
    """Chaos engineering test endpoint."""
    # Simulate potential failure scenarios
    
    # Randomly fail
    if random.random() < 0.1:  # 10% chance of failure
        raise Exception("Chaos test failure")
    
    # Simulate slow response
    if random.random() < 0.2:  # 20% chance of slow response
        await asyncio.sleep(random.uniform(0.5, 2.0))
    
    return {"status": "chaos_test_passed", "timestamp": time.time()}

@app.get("/concurrent")
async def concurrent_test(request):
    """Concurrent testing endpoint."""
    # Simulate concurrent processing
    await asyncio.sleep(0.05)
    
    return {
        "status": "concurrent_test_passed",
        "timestamp": time.time(),
        "thread_id": id(asyncio.current_task())
    }

@app.get("/memory")
async def memory_test(request):
    """Memory leak detection endpoint."""
    # Simulate memory usage tracking
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "status": "memory_check_completed",
        "memory_usage_mb": memory_info.rss / 1024 / 1024,
        "timestamp": time.time()
    }

@app.get("/test-report")
async def test_report(request):
    """Test reporting endpoint."""
    return {
        "status": "test_report_generated",
        "timestamp": time.time(),
        "metrics": {
            "total_tests": 100,
            "passed": 95,
            "failed": 5,
            "success_rate": 95.0
        },
        "summary": "All tests completed successfully"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("advanced_testing_app:app", host="0.0.0.0", port=8018, reload=False) 