#!/usr/bin/env python3
"""
QakeAPI Benchmark Script

Run benchmarks to measure QakeAPI performance.
Usage: python benchmarks/run_benchmarks.py

Requires: pip install httpx uvicorn
"""

import asyncio
import subprocess
import sys
import time
from typing import List, Tuple

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)


# Benchmark configuration
REQUESTS_COUNT = 2000
CONCURRENCY = 50
BASE_URL = "http://127.0.0.1:8000"
WARMUP_REQUESTS = 100


async def run_requests(client: httpx.AsyncClient, url: str, count: int) -> List[float]:
    """Run requests and return latencies in seconds."""
    latencies = []
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def single_request():
        async with semaphore:
            start = time.perf_counter()
            try:
                await client.get(url)
            except Exception:
                pass
            return time.perf_counter() - start

    tasks = [single_request() for _ in range(count)]
    latencies = await asyncio.gather(*tasks)
    return [l for l in latencies if l > 0]


def percentile(data: List[float], p: float) -> float:
    """Calculate percentile in ms."""
    if not data:
        return 0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_data) else f
    return (sorted_data[f] * (c - k) + sorted_data[c] * (k - f)) * 1000


async def benchmark_endpoint(name: str, url: str) -> dict:
    """Benchmark a single endpoint."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Warmup
        for _ in range(WARMUP_REQUESTS):
            try:
                await client.get(url)
            except Exception:
                pass

        # Actual benchmark
        start = time.perf_counter()
        latencies = await run_requests(client, url, REQUESTS_COUNT)
        elapsed = time.perf_counter() - start

    if not latencies:
        return {"name": name, "error": "No successful requests"}

    rps = len(latencies) / elapsed
    return {
        "name": name,
        "requests": len(latencies),
        "total_time": round(elapsed, 2),
        "rps": round(rps, 0),
        "p50_ms": round(percentile(latencies, 50), 2),
        "p95_ms": round(percentile(latencies, 95), 2),
        "p99_ms": round(percentile(latencies, 99), 2),
    }


def create_benchmark_app():
    """Create minimal QakeAPI app for benchmarking."""
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from qakeapi import QakeAPI

    app = QakeAPI(title="Benchmark", version="1.0")

    @app.get("/")
    def root():
        return {"message": "Hello"}

    @app.get("/users/{id}")
    def get_user(id: int):
        return {"id": id, "name": f"User {id}"}

    @app.get("/async")
    async def async_endpoint():
        return {"type": "async"}

    return app


def main():
    """Run benchmarks."""
    print("=" * 60)
    print("QakeAPI Benchmark")
    print("=" * 60)
    print(f"Requests: {REQUESTS_COUNT}, Concurrency: {CONCURRENCY}")
    print()

    # Start server in subprocess
    app = create_benchmark_app()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proc = subprocess.Popen(
        [sys.executable, "-c", """
import uvicorn
import sys
import os
os.chdir(r'""" + project_root.replace("\\", "\\\\") + """')
sys.path.insert(0, '.')
from benchmarks.run_benchmarks import create_benchmark_app
app = create_benchmark_app()
uvicorn.run(app, host='127.0.0.1', port=8000, log_level='error')
"""],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=project_root
    )

    # Wait for server to start
    time.sleep(2)

    try:
        results = asyncio.run(run_all_benchmarks())
        print_results(results)
    finally:
        proc.terminate()
        proc.wait(timeout=5)


async def run_all_benchmarks() -> List[dict]:
    """Run all benchmark scenarios."""
    endpoints = [
        ("Simple JSON (GET /)", f"{BASE_URL}/"),
        ("Path params (GET /users/1)", f"{BASE_URL}/users/1"),
        ("Async handler (GET /async)", f"{BASE_URL}/async"),
    ]
    results = []
    for name, url in endpoints:
        print(f"Benchmarking {name}...", end=" ", flush=True)
        result = await benchmark_endpoint(name, url)
        results.append(result)
        if "error" not in result:
            print(f"{result['rps']:.0f} RPS")
        else:
            print(result["error"])
    return results


def print_results(results: List[dict]):
    """Print benchmark results."""
    print()
    print("Results:")
    print("-" * 60)
    for r in results:
        if "error" in r:
            print(f"  {r['name']}: {r['error']}")
            continue
        print(f"  {r['name']}")
        print(f"    RPS: {r['rps']:.0f} | p50: {r['p50_ms']:.2f}ms | p99: {r['p99_ms']:.2f}ms")
    print("=" * 60)


if __name__ == "__main__":
    import os
    main()
