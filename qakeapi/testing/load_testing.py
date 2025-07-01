"""
Load testing integration for QakeAPI.
"""
import asyncio
import time
import statistics
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import aiohttp
import json

logger = logging.getLogger(__name__)


@dataclass
class LoadTestConfig:
    """Configuration for load testing."""
    url: str
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    data: Any = None
    concurrent_users: int = 10
    duration: float = 60.0
    ramp_up_time: float = 10.0
    ramp_down_time: float = 10.0
    timeout: float = 30.0
    verify_ssl: bool = True


@dataclass
class LoadTestResult:
    """Result of a load test."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    median_response_time: float
    requests_per_second: float
    error_rate: float
    status_codes: Dict[int, int]
    response_times: List[float]
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "total_time": self.total_time,
            "avg_response_time": self.avg_response_time,
            "min_response_time": self.min_response_time,
            "max_response_time": self.max_response_time,
            "median_response_time": self.median_response_time,
            "requests_per_second": self.requests_per_second,
            "error_rate": self.error_rate,
            "status_codes": self.status_codes,
            "errors": self.errors
        }


class LoadTester:
    """Load testing framework."""
    
    def __init__(self):
        self.results: List[LoadTestResult] = []
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=1000, limit_per_host=100)
        self._session = aiohttp.ClientSession(connector=connector)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    async def run_load_test(self, config: LoadTestConfig) -> LoadTestResult:
        """Run load test with given configuration."""
        logger.info(f"Starting load test: {config.concurrent_users} users for {config.duration}s")
        
        start_time = time.time()
        response_times = []
        status_codes = {}
        errors = []
        
        # Calculate ramp up/down parameters
        ramp_up_steps = max(1, int(config.ramp_up_time / 2))
        ramp_down_steps = max(1, int(config.ramp_down_time / 2))
        
        # Create tasks for concurrent users
        tasks = []
        for user_id in range(config.concurrent_users):
            task = asyncio.create_task(
                self._user_worker(user_id, config, response_times, status_codes, errors)
            )
            tasks.append(task)
            
            # Ramp up delay
            if user_id < ramp_up_steps:
                await asyncio.sleep(config.ramp_up_time / ramp_up_steps)
        
        # Wait for test duration
        await asyncio.sleep(config.duration)
        
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        
        # Wait for tasks to complete
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate statistics
        successful_requests = sum(1 for code in status_codes.values() if 200 <= code < 400)
        failed_requests = sum(1 for code in status_codes.values() if code >= 400)
        total_requests = len(response_times)
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            median_response_time = statistics.median(response_times)
        else:
            avg_response_time = min_response_time = max_response_time = median_response_time = 0
        
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        error_rate = failed_requests / total_requests if total_requests > 0 else 0
        
        # Create result
        result = LoadTestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time=total_time,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            median_response_time=median_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            status_codes=status_codes,
            response_times=response_times,
            errors=errors
        )
        
        self.results.append(result)
        logger.info(f"Load test completed: {total_requests} requests, {requests_per_second:.2f} req/s")
        
        return result
    
    async def _user_worker(
        self,
        user_id: int,
        config: LoadTestConfig,
        response_times: List[float],
        status_codes: Dict[int, int],
        errors: List[str]
    ) -> None:
        """Worker function for each virtual user."""
        logger.debug(f"Starting user worker {user_id}")
        
        while True:
            try:
                start_time = time.perf_counter()
                
                # Make HTTP request
                async with self._session.request(
                    method=config.method,
                    url=config.url,
                    headers=config.headers,
                    data=config.data,
                    timeout=aiohttp.ClientTimeout(total=config.timeout),
                    ssl=config.verify_ssl
                ) as response:
                    end_time = time.perf_counter()
                    response_time = end_time - start_time
                    
                    # Record response time
                    response_times.append(response_time)
                    
                    # Record status code
                    status_code = response.status
                    status_codes[status_code] = status_codes.get(status_code, 0) + 1
                    
                    # Log errors
                    if status_code >= 400:
                        error_msg = f"HTTP {status_code}: {config.url}"
                        errors.append(error_msg)
                        logger.warning(f"User {user_id}: {error_msg}")
                
                # Small delay between requests
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                end_time = time.perf_counter()
                response_time = end_time - start_time
                response_times.append(response_time)
                
                error_msg = f"Exception: {str(e)}"
                errors.append(error_msg)
                logger.error(f"User {user_id}: {error_msg}")
                
                # Small delay before retry
                await asyncio.sleep(1.0)
    
    def get_results(self) -> List[LoadTestResult]:
        """Get all load test results."""
        return self.results.copy()
    
    def clear_results(self) -> None:
        """Clear all load test results."""
        self.results.clear()
    
    def export_results(self, filename: str) -> None:
        """Export results to JSON file."""
        data = [result.to_dict() for result in self.results]
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Load test results exported to {filename}")
    
    def print_summary(self) -> None:
        """Print load test summary."""
        if not self.results:
            print("No load test results available")
            return
        
        print("\n" + "="*80)
        print("LOAD TEST SUMMARY")
        print("="*80)
        
        for i, result in enumerate(self.results):
            print(f"\nTest {i + 1}:")
            print(f"  Total Requests: {result.total_requests}")
            print(f"  Successful: {result.successful_requests}")
            print(f"  Failed: {result.failed_requests}")
            print(f"  Total Time: {result.total_time:.2f}s")
            print(f"  Requests/Second: {result.requests_per_second:.2f}")
            print(f"  Error Rate: {result.error_rate:.2%}")
            print(f"  Avg Response Time: {result.avg_response_time:.3f}s")
            print(f"  Min Response Time: {result.min_response_time:.3f}s")
            print(f"  Max Response Time: {result.max_response_time:.3f}s")
            print(f"  Median Response Time: {result.median_response_time:.3f}s")
            
            if result.status_codes:
                print("  Status Codes:")
                for code, count in sorted(result.status_codes.items()):
                    print(f"    {code}: {count}")
        
        print("\n" + "="*80)


# Predefined load test scenarios
def create_simple_load_test(url: str, users: int = 10, duration: float = 60.0) -> LoadTestConfig:
    """Create simple load test configuration."""
    return LoadTestConfig(
        url=url,
        method="GET",
        concurrent_users=users,
        duration=duration
    )


def create_api_load_test(
    url: str,
    method: str = "POST",
    data: Dict[str, Any] = None,
    users: int = 20,
    duration: float = 120.0
) -> LoadTestConfig:
    """Create API load test configuration."""
    headers = {"Content-Type": "application/json"}
    
    return LoadTestConfig(
        url=url,
        method=method,
        headers=headers,
        data=json.dumps(data) if data else None,
        concurrent_users=users,
        duration=duration
    )


def create_stress_test(url: str, users: int = 50, duration: float = 300.0) -> LoadTestConfig:
    """Create stress test configuration."""
    return LoadTestConfig(
        url=url,
        method="GET",
        concurrent_users=users,
        duration=duration,
        ramp_up_time=30.0,
        ramp_down_time=30.0
    )


def create_spike_test(url: str, users: int = 100, duration: float = 60.0) -> LoadTestConfig:
    """Create spike test configuration."""
    return LoadTestConfig(
        url=url,
        method="GET",
        concurrent_users=users,
        duration=duration,
        ramp_up_time=5.0,
        ramp_down_time=5.0
    )


# Context manager for load testing
@asynccontextmanager
async def load_test(config: LoadTestConfig):
    """Context manager for load testing."""
    async with LoadTester() as tester:
        result = await tester.run_load_test(config)
        yield result


# Decorator for load testing
def load_test_decorator(config: LoadTestConfig):
    """Decorator for load testing."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            async with load_test(config) as result:
                # Add result to kwargs
                kwargs['load_test_result'] = result
                
                # Run original function
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Utility functions for load testing
async def quick_load_test(url: str, users: int = 5, duration: float = 10.0) -> LoadTestResult:
    """Quick load test for development."""
    config = LoadTestConfig(
        url=url,
        concurrent_users=users,
        duration=duration
    )
    
    async with LoadTester() as tester:
        return await tester.run_load_test(config)


async def benchmark_load_test(
    url: str,
    users_range: List[int] = [1, 5, 10, 20, 50],
    duration: float = 30.0
) -> List[LoadTestResult]:
    """Run load tests with different user counts."""
    results = []
    
    async with LoadTester() as tester:
        for users in users_range:
            config = LoadTestConfig(
                url=url,
                concurrent_users=users,
                duration=duration
            )
            
            result = await tester.run_load_test(config)
            results.append(result)
            
            logger.info(f"Benchmark completed for {users} users: {result.requests_per_second:.2f} req/s")
    
    return results 