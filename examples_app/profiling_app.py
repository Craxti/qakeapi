# -*- coding: utf-8 -*-
"""
Profiling example with QakeAPI.
"""
import sys
import os
import time
import cProfile
import pstats
import io
from datetime import datetime
from typing import Dict, Any

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import Field

# Initialize application
app = Application(
    title="Profiling Example",
    version="1.0.3",
    description="Performance profiling example with QakeAPI"
)

# Pydantic models
class ProfilingRequest(RequestModel):
    """Profiling request model"""
    iterations: int = Field(..., ge=1, le=1000000, description="Number of iterations")
    complexity: str = Field(..., description="Computation complexity", pattern="^(simple|medium|complex)$")

# Profiling data storage
profiling_data = []

def simple_computation(iterations: int) -> float:
    """Simple computation for profiling"""
    result = 0.0
    for i in range(iterations):
        result += i * 0.1
    return result

def medium_computation(iterations: int) -> float:
    """Medium complexity computation for profiling"""
    result = 0.0
    for i in range(iterations):
        result += (i ** 2) * 0.01
        if i % 1000 == 0:
            result = result ** 0.5
    return result

def complex_computation(iterations: int) -> float:
    """Complex computation for profiling"""
    result = 0.0
    for i in range(iterations):
        result += (i ** 3) * 0.001
        if i % 100 == 0:
            result = result ** 0.33
            result = result * 1.1
    return result

def profile_function(func, *args, **kwargs):
    """Profile a function and return statistics"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    profiler.disable()
    
    # Get profiling statistics
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
    
    return {
        "result": result,
        "execution_time": end_time - start_time,
        "profiling_stats": s.getvalue()
    }

@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "Profiling API is running",
        "endpoints": {
            "/fast": "GET - Fast computation profiling",
            "/medium": "GET - Medium complexity profiling", 
            "/complex": "GET - Complex computation profiling",
            "/profile": "POST - Custom profiling with parameters",
            "/stats": "GET - Profiling statistics"
        }
    }

@app.get("/fast")
async def fast_computation(request: Request):
    """Fast computation profiling"""
    iterations = 10000
    
    profile_result = profile_function(simple_computation, iterations)
    
    profiling_data.append({
        "type": "fast",
        "iterations": iterations,
        "execution_time": profile_result["execution_time"],
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {
        "message": "Fast computation completed",
        "iterations": iterations,
        "result": profile_result["result"],
        "execution_time": f"{profile_result['execution_time']:.4f}s",
        "profiling_stats": profile_result["profiling_stats"]
    }

@app.get("/medium")
async def medium_computation_endpoint(request: Request):
    """Medium complexity computation profiling"""
    iterations = 5000
    
    profile_result = profile_function(medium_computation, iterations)
    
    profiling_data.append({
        "type": "medium",
        "iterations": iterations,
        "execution_time": profile_result["execution_time"],
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {
        "message": "Medium complexity computation completed",
        "iterations": iterations,
        "result": profile_result["result"],
        "execution_time": f"{profile_result['execution_time']:.4f}s",
        "profiling_stats": profile_result["profiling_stats"]
    }

@app.get("/complex")
async def complex_computation_endpoint(request: Request):
    """Complex computation profiling"""
    iterations = 1000
    
    profile_result = profile_function(complex_computation, iterations)
    
    profiling_data.append({
        "type": "complex",
        "iterations": iterations,
        "execution_time": profile_result["execution_time"],
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {
        "message": "Complex computation completed",
        "iterations": iterations,
        "result": profile_result["result"],
        "execution_time": f"{profile_result['execution_time']:.4f}s",
        "profiling_stats": profile_result["profiling_stats"]
    }

@app.post("/profile")
@validate_request_body(ProfilingRequest)
async def custom_profiling(request: Request):
    """Custom profiling with user-defined parameters"""
    profiling_data_request = request.validated_data
    
    # Select computation function based on complexity
    if profiling_data_request.complexity == "simple":
        func = simple_computation
    elif profiling_data_request.complexity == "medium":
        func = medium_computation
    else:  # complex
        func = complex_computation
    
    profile_result = profile_function(func, profiling_data_request.iterations)
    
    profiling_data.append({
        "type": profiling_data_request.complexity,
        "iterations": profiling_data_request.iterations,
        "execution_time": profile_result["execution_time"],
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {
        "message": f"Custom {profiling_data_request.complexity} computation completed",
        "iterations": profiling_data_request.iterations,
        "complexity": profiling_data_request.complexity,
        "result": profile_result["result"],
        "execution_time": f"{profile_result['execution_time']:.4f}s",
        "profiling_stats": profile_result["profiling_stats"]
    }

@app.get("/stats")
async def get_profiling_stats(request: Request):
    """Get profiling statistics"""
    if not profiling_data:
        return {
            "message": "No profiling data available",
            "total_runs": 0
        }
    
    # Calculate statistics
    total_runs = len(profiling_data)
    avg_execution_time = sum(d["execution_time"] for d in profiling_data) / total_runs
    
    # Group by type
    type_stats = {}
    for data in profiling_data:
        comp_type = data["type"]
        if comp_type not in type_stats:
            type_stats[comp_type] = {
                "count": 0,
                "total_time": 0,
                "avg_time": 0
            }
        type_stats[comp_type]["count"] += 1
        type_stats[comp_type]["total_time"] += data["execution_time"]
    
    # Calculate averages for each type
    for comp_type in type_stats:
        type_stats[comp_type]["avg_time"] = (
            type_stats[comp_type]["total_time"] / type_stats[comp_type]["count"]
        )
    
    return {
        "message": "Profiling statistics",
        "total_runs": total_runs,
        "average_execution_time": f"{avg_execution_time:.4f}s",
        "type_statistics": type_stats,
        "recent_runs": profiling_data[-10:]  # Last 10 runs
    }

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "profiling_runs": len(profiling_data)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8012) 