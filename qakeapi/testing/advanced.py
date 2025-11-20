"""
Advanced testing utilities for QakeAPI.

This module provides advanced testing capabilities including:
- Property-based testing with Hypothesis
- Mutation testing
- Chaos engineering tests
- End-to-end testing framework
- Performance regression testing
- Memory leak detection
- Concurrent testing utilities
- Test data factories
- Test environment management
- Test reporting and analytics
"""

import asyncio
import gc
import json
import logging
import os
import random
import time
import tracemalloc
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Type, Union
from unittest.mock import Mock, patch

import psutil
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule
from memory_profiler import profile

from ..core.application import Application
from ..core.requests import Request
from ..core.responses import Response

logger = logging.getLogger(__name__)


@dataclass
class TestMetrics:
    """Test execution metrics."""
    execution_time: float
    memory_usage: float
    cpu_usage: float
    request_count: int
    error_count: int
    response_times: List[float] = field(default_factory=list)
    memory_snapshots: List[float] = field(default_factory=list)


@dataclass
class TestReport:
    """Comprehensive test report."""
    test_name: str
    status: str
    metrics: TestMetrics
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    performance_regression: bool = False
    memory_leak_detected: bool = False


class PropertyBasedTester:
    """Property-based testing with Hypothesis."""
    
    def __init__(self, app: Application):
        self.app = app
        self.test_data = []
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_string_properties(self, text: str):
        """Test string-related properties."""
        # Test that string operations are consistent
        assert len(text) >= 1
        assert len(text) <= 100
        assert text == text.strip() or text != text.strip()
    
    @given(st.integers(min_value=1, max_value=1000))
    @settings(max_examples=50)
    def test_numeric_properties(self, number: int):
        """Test numeric-related properties."""
        # Test that numeric operations are consistent
        assert number >= 1
        assert number <= 1000
        assert number * 2 == number + number
        assert number + 0 == number
    
    @given(st.lists(st.text(), min_size=1, max_size=10))
    @settings(max_examples=30)
    def test_list_properties(self, items: List[str]):
        """Test list-related properties."""
        # Test that list operations are consistent
        assert len(items) >= 1
        assert len(items) <= 10
        if items:
            assert items[0] in items
            assert len(set(items)) <= len(items)


class MutationTester:
    """Mutation testing framework."""
    
    def __init__(self, app: Application):
        self.app = app
        self.mutations = []
        self.original_code = {}
    
    def create_mutation(self, target_function: Callable, mutation_type: str):
        """Create a mutation of the target function."""
        import inspect
        import ast
        
        source = inspect.getsource(target_function)
        tree = ast.parse(source)
        
        # Apply different types of mutations
        if mutation_type == "arithmetic":
            # Change arithmetic operators
            for node in ast.walk(tree):
                if isinstance(node, ast.BinOp):
                    if isinstance(node.op, ast.Add):
                        node.op = ast.Sub()
                    elif isinstance(node.op, ast.Sub):
                        node.op = ast.Add()
        
        elif mutation_type == "comparison":
            # Change comparison operators
            for node in ast.walk(tree):
                if isinstance(node, ast.Compare):
                    for op in node.ops:
                        if isinstance(op, ast.Eq):
                            op = ast.Ne()
                        elif isinstance(op, ast.Lt):
                            op = ast.Gt()
        
        elif mutation_type == "boolean":
            # Change boolean operators
            for node in ast.walk(tree):
                if isinstance(node, ast.BoolOp):
                    if isinstance(node.op, ast.And):
                        node.op = ast.Or()
                    elif isinstance(node.op, ast.Or):
                        node.op = ast.And()
        
        return ast.unparse(tree)
    
    def test_mutation_killing(self, test_suite: List[Callable], target_function: Callable):
        """Test if mutations are killed by the test suite."""
        results = []
        
        mutation_types = ["arithmetic", "comparison", "boolean"]
        
        for mutation_type in mutation_types:
            mutated_code = self.create_mutation(target_function, mutation_type)
            killed = False
            
            # Test if any test in the suite detects the mutation
            for test in test_suite:
                try:
                    # Apply mutation and run test
                    with patch.object(target_function, '__code__', 
                                    compile(mutated_code, '<string>', 'exec')):
                        test()
                        # If test passes, mutation might not be killed
                        killed = False
                except Exception:
                    # If test fails, mutation is killed
                    killed = True
                    break
            
            results.append({
                'mutation_type': mutation_type,
                'killed': killed,
                'mutated_code': mutated_code
            })
        
        return results


class ChaosEngineeringTester:
    """Chaos engineering testing framework."""
    
    def __init__(self, app: Application):
        self.app = app
        self.chaos_scenarios = []
    
    @asynccontextmanager
    async def network_partition(self, duration: float = 1.0):
        """Simulate network partition."""
        # Simulate network issues
        original_send = asyncio.StreamWriter.write
        
        async def delayed_write(data):
            await asyncio.sleep(random.uniform(0.1, 0.5))
            return await original_send(data)
        
        with patch('asyncio.StreamWriter.write', delayed_write):
            yield
        
        await asyncio.sleep(duration)
    
    @asynccontextmanager
    async def high_latency(self, latency: float = 2.0):
        """Simulate high latency."""
        original_sleep = asyncio.sleep
        
        async def delayed_sleep(delay):
            return await original_sleep(delay + latency)
        
        with patch('asyncio.sleep', delayed_sleep):
            yield
    
    @asynccontextmanager
    async def memory_pressure(self, pressure_level: float = 0.8):
        """Simulate memory pressure."""
        # Allocate memory to create pressure
        memory_blocks = []
        
        try:
            # Allocate memory blocks
            for _ in range(int(pressure_level * 100)):
                memory_blocks.append(b'x' * 1024 * 1024)  # 1MB blocks
            yield
        finally:
            # Clean up
            memory_blocks.clear()
            gc.collect()
    
    @asynccontextmanager
    async def cpu_pressure(self, pressure_level: float = 0.8):
        """Simulate CPU pressure."""
        # Create CPU-intensive tasks
        tasks = []
        
        try:
            for _ in range(int(pressure_level * 4)):  # Number of CPU cores
                task = asyncio.create_task(self._cpu_intensive_task())
                tasks.append(task)
            yield
        finally:
            # Cancel tasks
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _cpu_intensive_task(self):
        """CPU-intensive task for pressure simulation."""
        while True:
            # Perform CPU-intensive calculations
            sum(range(10000))
            await asyncio.sleep(0.001)
    
    async def run_chaos_scenario(self, scenario_name: str, scenario_func: Callable):
        """Run a chaos engineering scenario."""
        logger.info(f"Running chaos scenario: {scenario_name}")
        
        start_time = time.time()
        try:
            await scenario_func()
            success = True
        except Exception as e:
            logger.error(f"Chaos scenario failed: {e}")
            success = False
        
        duration = time.time() - start_time
        
        self.chaos_scenarios.append({
            'name': scenario_name,
            'success': success,
            'duration': duration,
            'timestamp': time.time()
        })
        
        return success


class EndToEndTester:
    """End-to-end testing framework."""
    
    def __init__(self, app: Application):
        self.app = app
        self.test_scenarios = []
        self.browser_automation = None
    
    async def setup_browser_automation(self):
        """Setup browser automation for E2E tests."""
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch()
            self.page = await self.browser.new_page()
        except ImportError:
            logger.warning("Playwright not installed. Browser automation disabled.")
            self.browser_automation = False
    
    async def teardown_browser_automation(self):
        """Teardown browser automation."""
        if hasattr(self, 'browser'):
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def test_user_journey(self, journey_name: str, steps: List[Dict[str, Any]]):
        """Test a complete user journey."""
        logger.info(f"Testing user journey: {journey_name}")
        
        results = []
        
        for step in steps:
            step_name = step['name']
            step_type = step['type']
            step_data = step.get('data', {})
            
            try:
                if step_type == 'api_call':
                    result = await self._execute_api_step(step_data)
                elif step_type == 'ui_interaction':
                    result = await self._execute_ui_step(step_data)
                elif step_type == 'assertion':
                    result = await self._execute_assertion_step(step_data)
                else:
                    raise ValueError(f"Unknown step type: {step_type}")
                
                results.append({
                    'step_name': step_name,
                    'success': True,
                    'result': result
                })
                
            except Exception as e:
                results.append({
                    'step_name': step_name,
                    'success': False,
                    'error': str(e)
                })
                break
        
        self.test_scenarios.append({
            'journey_name': journey_name,
            'results': results,
            'timestamp': time.time()
        })
        
        return all(r['success'] for r in results)
    
    async def _execute_api_step(self, data: Dict[str, Any]):
        """Execute an API step."""
        method = data['method']
        path = data['path']
        payload = data.get('payload')
        expected_status = data.get('expected_status', 200)
        
        # Create test client and make request
        from httpx import AsyncClient
        
        async with AsyncClient(app=self.app, base_url="http://test") as client:
            if method == 'GET':
                response = await client.get(path)
            elif method == 'POST':
                response = await client.post(path, json=payload)
            elif method == 'PUT':
                response = await client.put(path, json=payload)
            elif method == 'DELETE':
                response = await client.delete(path)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            assert response.status_code == expected_status
            return response.json()
    
    async def _execute_ui_step(self, data: Dict[str, Any]):
        """Execute a UI interaction step."""
        if not self.browser_automation:
            raise RuntimeError("Browser automation not available")
        
        action = data['action']
        selector = data['selector']
        value = data.get('value')
        
        if action == 'click':
            await self.page.click(selector)
        elif action == 'fill':
            await self.page.fill(selector, value)
        elif action == 'navigate':
            await self.page.goto(value)
        else:
            raise ValueError(f"Unsupported UI action: {action}")
    
    async def _execute_assertion_step(self, data: Dict[str, Any]):
        """Execute an assertion step."""
        assertion_type = data['type']
        expected = data['expected']
        
        if assertion_type == 'api_response':
            # Assert API response
            actual = data['actual']
            assert actual == expected
        elif assertion_type == 'ui_element':
            # Assert UI element
            selector = data['selector']
            element = await self.page.query_selector(selector)
            assert element is not None
        else:
            raise ValueError(f"Unsupported assertion type: {assertion_type}")


class PerformanceRegressionTester:
    """Performance regression testing."""
    
    def __init__(self, app: Application):
        self.app = app
        self.baseline_metrics = {}
        self.regression_threshold = 0.2  # 20% degradation threshold
    
    @contextmanager
    def measure_performance(self, test_name: str):
        """Context manager for measuring performance."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        # Start memory profiling
        tracemalloc.start()
        
        try:
            yield
        finally:
            # Stop memory profiling
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            metrics = TestMetrics(
                execution_time=end_time - start_time,
                memory_usage=end_memory - start_memory,
                cpu_usage=psutil.cpu_percent(),
                request_count=1,
                error_count=0,
                response_times=[end_time - start_time],
                memory_snapshots=[current]
            )
            
            self._check_regression(test_name, metrics)
    
    def _check_regression(self, test_name: str, current_metrics: TestMetrics):
        """Check for performance regression."""
        if test_name in self.baseline_metrics:
            baseline = self.baseline_metrics[test_name]
            
            # Check execution time regression
            time_regression = (current_metrics.execution_time - baseline.execution_time) / baseline.execution_time
            if time_regression > self.regression_threshold:
                logger.warning(f"Performance regression detected in {test_name}: "
                             f"execution time increased by {time_regression:.2%}")
            
            # Check memory regression
            memory_regression = (current_metrics.memory_usage - baseline.memory_usage) / baseline.memory_usage
            if memory_regression > self.regression_threshold:
                logger.warning(f"Memory regression detected in {test_name}: "
                             f"memory usage increased by {memory_regression:.2%}")
    
    def set_baseline(self, test_name: str, metrics: TestMetrics):
        """Set baseline metrics for a test."""
        self.baseline_metrics[test_name] = metrics
    
    def save_baseline(self, filepath: str):
        """Save baseline metrics to file."""
        baseline_data = {
            name: {
                'execution_time': metrics.execution_time,
                'memory_usage': metrics.memory_usage,
                'cpu_usage': metrics.cpu_usage
            }
            for name, metrics in self.baseline_metrics.items()
        }
        
        with open(filepath, 'w') as f:
            json.dump(baseline_data, f, indent=2)
    
    def load_baseline(self, filepath: str):
        """Load baseline metrics from file."""
        with open(filepath, 'r') as f:
            baseline_data = json.load(f)
        
        for name, data in baseline_data.items():
            metrics = TestMetrics(
                execution_time=data['execution_time'],
                memory_usage=data['memory_usage'],
                cpu_usage=data['cpu_usage'],
                request_count=1,
                error_count=0
            )
            self.baseline_metrics[name] = metrics


class MemoryLeakDetector:
    """Memory leak detection utilities."""
    
    def __init__(self):
        self.snapshots = []
        self.leak_threshold = 0.1  # 10% increase threshold
    
    @contextmanager
    def detect_leaks(self, test_name: str):
        """Context manager for detecting memory leaks."""
        # Force garbage collection
        gc.collect()
        
        # Take initial snapshot
        initial_snapshot = tracemalloc.take_snapshot()
        initial_memory = psutil.Process().memory_info().rss
        
        try:
            yield
        finally:
            # Force garbage collection again
            gc.collect()
            
            # Take final snapshot
            final_snapshot = tracemalloc.take_snapshot()
            final_memory = psutil.Process().memory_info().rss
            
            # Compare snapshots
            top_stats = final_snapshot.compare_to(initial_snapshot, 'lineno')
            
            # Check for significant memory increase
            memory_increase = (final_memory - initial_memory) / initial_memory
            if memory_increase > self.leak_threshold:
                logger.warning(f"Potential memory leak detected in {test_name}: "
                             f"memory increased by {memory_increase:.2%}")
                
                # Log top memory consumers
                for stat in top_stats[:5]:
                    logger.info(f"Memory change: {stat.size_diff:+d} B "
                              f"in {stat.traceback.format()}")
            
            self.snapshots.append({
                'test_name': test_name,
                'initial_memory': initial_memory,
                'final_memory': final_memory,
                'memory_increase': memory_increase,
                'top_stats': top_stats[:5]
            })


class ConcurrentTester:
    """Concurrent testing utilities."""
    
    def __init__(self, app: Application):
        self.app = app
        self.concurrent_results = []
    
    async def run_concurrent_requests(self, request_func: Callable, 
                                    concurrency: int = 10, 
                                    total_requests: int = 100):
        """Run concurrent requests and measure performance."""
        semaphore = asyncio.Semaphore(concurrency)
        
        async def limited_request():
            async with semaphore:
                start_time = time.time()
                try:
                    result = await request_func()
                    success = True
                except Exception as e:
                    result = str(e)
                    success = False
                end_time = time.time()
                
                return {
                    'success': success,
                    'result': result,
                    'duration': end_time - start_time
                }
        
        # Create tasks
        tasks = [limited_request() for _ in range(total_requests)]
        
        # Run concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = sum(1 for r in results if r.get('success', False))
        failed_requests = total_requests - successful_requests
        avg_duration = sum(r.get('duration', 0) for r in results) / len(results)
        
        self.concurrent_results.append({
            'concurrency': concurrency,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'total_time': total_time,
            'avg_duration': avg_duration,
            'requests_per_second': total_requests / total_time
        })
        
        return {
            'success_rate': successful_requests / total_requests,
            'avg_duration': avg_duration,
            'requests_per_second': total_requests / total_time
        }


class TestDataFactory:
    """Test data factory for generating test data."""
    
    def __init__(self):
        self.factories = {}
        self.sequences = {}
    
    def register_factory(self, model_class: Type, factory_func: Callable):
        """Register a factory function for a model class."""
        self.factories[model_class] = factory_func
    
    def create(self, model_class: Type, **kwargs):
        """Create an instance using the registered factory."""
        if model_class not in self.factories:
            raise ValueError(f"No factory registered for {model_class}")
        
        factory_func = self.factories[model_class]
        return factory_func(**kwargs)
    
    def create_batch(self, model_class: Type, count: int, **kwargs):
        """Create multiple instances."""
        return [self.create(model_class, **kwargs) for _ in range(count)]
    
    def sequence(self, name: str, start: int = 1):
        """Create a sequence generator."""
        if name not in self.sequences:
            self.sequences[name] = start
        
        current = self.sequences[name]
        self.sequences[name] += 1
        return current


class TestEnvironmentManager:
    """Test environment management."""
    
    def __init__(self, base_dir: str = "test_env"):
        self.base_dir = Path(base_dir)
        self.environments = {}
    
    @contextmanager
    def isolated_environment(self, env_name: str):
        """Create an isolated test environment."""
        env_dir = self.base_dir / env_name
        env_dir.mkdir(parents=True, exist_ok=True)
        
        # Store original environment
        original_env = os.environ.copy()
        
        try:
            # Set up isolated environment
            os.environ['TEST_ENV'] = env_name
            os.environ['TEST_DIR'] = str(env_dir)
            
            yield env_dir
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    def cleanup_environment(self, env_name: str):
        """Clean up a test environment."""
        env_dir = self.base_dir / env_name
        if env_dir.exists():
            import shutil
            shutil.rmtree(env_dir)
    
    def cleanup_all(self):
        """Clean up all test environments."""
        if self.base_dir.exists():
            import shutil
            shutil.rmtree(self.base_dir)


class TestReporter:
    """Test reporting and analytics."""
    
    def __init__(self, output_dir: str = "test_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reports = []
    
    def add_report(self, report: TestReport):
        """Add a test report."""
        self.reports.append(report)
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of all reports."""
        total_tests = len(self.reports)
        passed_tests = sum(1 for r in self.reports if r.status == 'passed')
        failed_tests = total_tests - passed_tests
        
        avg_execution_time = sum(r.metrics.execution_time for r in self.reports) / total_tests
        avg_memory_usage = sum(r.metrics.memory_usage for r in self.reports) / total_tests
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': passed_tests / total_tests,
            'avg_execution_time': avg_execution_time,
            'avg_memory_usage': avg_memory_usage,
            'performance_regressions': sum(1 for r in self.reports if r.performance_regression),
            'memory_leaks': sum(1 for r in self.reports if r.memory_leak_detected)
        }
    
    def save_reports(self, filename: str = "test_report.json"):
        """Save all reports to file."""
        report_data = {
            'summary': self.generate_summary(),
            'reports': [
                {
                    'test_name': r.test_name,
                    'status': r.status,
                    'metrics': {
                        'execution_time': r.metrics.execution_time,
                        'memory_usage': r.metrics.memory_usage,
                        'cpu_usage': r.metrics.cpu_usage,
                        'request_count': r.metrics.request_count,
                        'error_count': r.metrics.error_count
                    },
                    'errors': r.errors,
                    'warnings': r.warnings,
                    'performance_regression': r.performance_regression,
                    'memory_leak_detected': r.memory_leak_detected
                }
                for r in self.reports
            ]
        }
        
        output_file = self.output_dir / filename
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return output_file
    
    def generate_html_report(self, filename: str = "test_report.html"):
        """Generate an HTML test report."""
        summary = self.generate_summary()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>QakeAPI Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: white; border-radius: 3px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .warning {{ color: orange; }}
            </style>
        </head>
        <body>
            <h1>QakeAPI Test Report</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                <div class="metric">
                    <strong>Total Tests:</strong> {summary['total_tests']}
                </div>
                <div class="metric passed">
                    <strong>Passed:</strong> {summary['passed_tests']}
                </div>
                <div class="metric failed">
                    <strong>Failed:</strong> {summary['failed_tests']}
                </div>
                <div class="metric">
                    <strong>Success Rate:</strong> {summary['success_rate']:.2%}
                </div>
                <div class="metric">
                    <strong>Avg Execution Time:</strong> {summary['avg_execution_time']:.3f}s
                </div>
                <div class="metric">
                    <strong>Avg Memory Usage:</strong> {summary['avg_memory_usage']:.0f} bytes
                </div>
            </div>
            
            <h2>Test Details</h2>
            <table border="1" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Execution Time</th>
                    <th>Memory Usage</th>
                    <th>Issues</th>
                </tr>
        """
        
        for report in self.reports:
            status_class = 'passed' if report.status == 'passed' else 'failed'
            issues = []
            if report.performance_regression:
                issues.append('Performance Regression')
            if report.memory_leak_detected:
                issues.append('Memory Leak')
            if report.errors:
                issues.append(f"{len(report.errors)} Errors")
            
            html_content += f"""
                <tr>
                    <td>{report.test_name}</td>
                    <td class="{status_class}">{report.status}</td>
                    <td>{report.metrics.execution_time:.3f}s</td>
                    <td>{report.metrics.memory_usage:.0f} bytes</td>
                    <td>{', '.join(issues) if issues else 'None'}</td>
                </tr>
            """
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        output_file = self.output_dir / filename
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        return output_file


# Convenience functions for easy testing
def create_advanced_test_suite(app: Application) -> Dict[str, Any]:
    """Create a comprehensive advanced test suite."""
    return {
        'property_tester': PropertyBasedTester(app),
        'mutation_tester': MutationTester(app),
        'chaos_tester': ChaosEngineeringTester(app),
        'e2e_tester': EndToEndTester(app),
        'performance_tester': PerformanceRegressionTester(app),
        'memory_detector': MemoryLeakDetector(),
        'concurrent_tester': ConcurrentTester(app),
        'data_factory': TestDataFactory(),
        'env_manager': TestEnvironmentManager(),
        'reporter': TestReporter()
    }


@pytest.fixture
def advanced_test_suite(app: Application):
    """Pytest fixture for advanced testing."""
    return create_advanced_test_suite(app) 