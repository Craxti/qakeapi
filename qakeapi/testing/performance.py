"""
Performance testing framework with benchmarks for QakeAPI.
"""
import asyncio
import time
import statistics
import psutil
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from functools import wraps
from contextlib import asynccontextmanager
import json

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    median_time: float
    std_dev: float
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time": self.total_time,
            "avg_time": self.avg_time,
            "min_time": self.min_time,
            "max_time": self.max_time,
            "median_time": self.median_time,
            "std_dev": self.std_dev,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "metadata": self.metadata
        }


class PerformanceTester:
    """Performance testing framework."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self._current_test: Optional[str] = None
    
    async def benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = 100,
        warmup_iterations: int = 10,
        measure_memory: bool = True,
        measure_cpu: bool = True,
        **kwargs
    ) -> BenchmarkResult:
        """Run performance benchmark."""
        logger.info(f"Starting benchmark: {name} ({iterations} iterations)")
        
        # Warmup
        if warmup_iterations > 0:
            logger.debug(f"Warming up with {warmup_iterations} iterations")
            for _ in range(warmup_iterations):
                if asyncio.iscoroutinefunction(func):
                    await func(**kwargs)
                else:
                    func(**kwargs)
        
        # Measure memory before
        memory_before = None
        if measure_memory:
            memory_before = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Run benchmark
        times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            
            if asyncio.iscoroutinefunction(func):
                await func(**kwargs)
            else:
                func(**kwargs)
            
            end_time = time.perf_counter()
            times.append(end_time - start_time)
            
            if (i + 1) % 10 == 0:
                logger.debug(f"Completed {i + 1}/{iterations} iterations")
        
        # Measure memory after
        memory_after = None
        if measure_memory:
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Calculate statistics
        total_time = sum(times)
        avg_time = total_time / iterations
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        
        # Calculate memory usage
        memory_usage = None
        if memory_before and memory_after:
            memory_usage = memory_after - memory_before
        
        # Create result
        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            std_dev=std_dev,
            memory_usage=memory_usage,
            cpu_usage=None,  # TODO: Implement CPU measurement
            metadata=kwargs
        )
        
        self.results.append(result)
        logger.info(f"Benchmark completed: {name} - Avg: {avg_time:.6f}s")
        
        return result
    
    def get_result(self, name: str) -> Optional[BenchmarkResult]:
        """Get benchmark result by name."""
        for result in self.results:
            if result.name == name:
                return result
        return None
    
    def get_results(self) -> List[BenchmarkResult]:
        """Get all benchmark results."""
        return self.results.copy()
    
    def clear_results(self) -> None:
        """Clear all benchmark results."""
        self.results.clear()
    
    def export_results(self, filename: str) -> None:
        """Export results to JSON file."""
        data = [result.to_dict() for result in self.results]
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Results exported to {filename}")
    
    def print_summary(self) -> None:
        """Print benchmark summary."""
        if not self.results:
            print("No benchmark results available")
            return
        
        print("\n" + "="*80)
        print("PERFORMANCE BENCHMARK SUMMARY")
        print("="*80)
        
        for result in self.results:
            print(f"\n{result.name}:")
            print(f"  Iterations: {result.iterations}")
            print(f"  Total Time: {result.total_time:.6f}s")
            print(f"  Average Time: {result.avg_time:.6f}s")
            print(f"  Min Time: {result.min_time:.6f}s")
            print(f"  Max Time: {result.max_time:.6f}s")
            print(f"  Median Time: {result.median_time:.6f}s")
            print(f"  Std Dev: {result.std_dev:.6f}s")
            
            if result.memory_usage:
                print(f"  Memory Usage: {result.memory_usage:.2f} MB")
        
        print("\n" + "="*80)


class BenchmarkSuite:
    """Suite of performance benchmarks."""
    
    def __init__(self, name: str):
        self.name = name
        self.tester = PerformanceTester()
        self.benchmarks: List[Tuple[str, Callable, Dict[str, Any]]] = []
    
    def add_benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = 100,
        warmup_iterations: int = 10,
        measure_memory: bool = True,
        **kwargs
    ) -> None:
        """Add benchmark to suite."""
        self.benchmarks.append((
            name,
            func,
            {
                "iterations": iterations,
                "warmup_iterations": warmup_iterations,
                "measure_memory": measure_memory,
                **kwargs
            }
        ))
    
    async def run_all(self) -> List[BenchmarkResult]:
        """Run all benchmarks in suite."""
        logger.info(f"Running benchmark suite: {self.name}")
        
        results = []
        for name, func, config in self.benchmarks:
            result = await self.tester.benchmark(name, func, **config)
            results.append(result)
        
        logger.info(f"Benchmark suite completed: {self.name}")
        return results
    
    def get_results(self) -> List[BenchmarkResult]:
        """Get all benchmark results."""
        return self.tester.get_results()
    
    def print_summary(self) -> None:
        """Print benchmark suite summary."""
        print(f"\nBENCHMARK SUITE: {self.name}")
        self.tester.print_summary()


# Decorator for performance testing
def benchmark(
    name: Optional[str] = None,
    iterations: int = 100,
    warmup_iterations: int = 10,
    measure_memory: bool = True
):
    """Decorator for performance benchmarking."""
    def decorator(func: Callable) -> Callable:
        benchmark_name = name or func.__name__
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tester = PerformanceTester()
            result = await tester.benchmark(
                benchmark_name,
                func,
                iterations=iterations,
                warmup_iterations=warmup_iterations,
                measure_memory=measure_memory,
                *args,
                **kwargs
            )
            
            # Print result
            print(f"\nBenchmark: {result.name}")
            print(f"Average Time: {result.avg_time:.6f}s")
            print(f"Min Time: {result.min_time:.6f}s")
            print(f"Max Time: {result.max_time:.6f}s")
            
            if result.memory_usage:
                print(f"Memory Usage: {result.memory_usage:.2f} MB")
            
            return result
        
        return wrapper
    return decorator


# Context manager for performance testing
@asynccontextmanager
async def performance_test(name: str = "performance_test"):
    """Context manager for performance testing."""
    tester = PerformanceTester()
    try:
        yield tester
    finally:
        tester.print_summary()


# Utility functions for performance testing
async def measure_time(func: Callable, *args, **kwargs) -> float:
    """Measure execution time of a function."""
    start_time = time.perf_counter()
    
    if asyncio.iscoroutinefunction(func):
        await func(*args, **kwargs)
    else:
        func(*args, **kwargs)
    
    end_time = time.perf_counter()
    return end_time - start_time


def measure_memory_usage() -> float:
    """Measure current memory usage in MB."""
    return psutil.Process().memory_info().rss / 1024 / 1024


async def stress_test(
    func: Callable,
    concurrent_tasks: int = 10,
    duration: float = 30.0,
    **kwargs
) -> Dict[str, Any]:
    """Run stress test with concurrent tasks."""
    logger.info(f"Starting stress test: {concurrent_tasks} tasks for {duration}s")
    
    start_time = time.time()
    results = []
    
    async def worker():
        task_results = []
        while time.time() - start_time < duration:
            task_start = time.perf_counter()
            
            if asyncio.iscoroutinefunction(func):
                await func(**kwargs)
            else:
                func(**kwargs)
            
            task_end = time.perf_counter()
            task_results.append(task_end - task_start)
        
        return task_results
    
    # Create concurrent tasks
    tasks = [worker() for _ in range(concurrent_tasks)]
    worker_results = await asyncio.gather(*tasks)
    
    # Combine all results
    for worker_result in worker_results:
        results.extend(worker_result)
    
    # Calculate statistics
    total_requests = len(results)
    total_time = time.time() - start_time
    avg_time = sum(results) / total_requests if results else 0
    min_time = min(results) if results else 0
    max_time = max(results) if results else 0
    requests_per_second = total_requests / total_time
    
    return {
        "total_requests": total_requests,
        "total_time": total_time,
        "avg_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "requests_per_second": requests_per_second,
        "concurrent_tasks": concurrent_tasks
    } 