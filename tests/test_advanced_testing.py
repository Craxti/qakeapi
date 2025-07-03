"""
Tests for advanced testing functionality.

This module tests the advanced testing capabilities including:
- Property-based testing
- Mutation testing
- Chaos engineering
- End-to-end testing
- Performance regression testing
- Memory leak detection
- Concurrent testing
- Test data factories
- Test environment management
- Test reporting
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, settings, strategies as st

from qakeapi import Application
from qakeapi.testing.advanced import (
    ChaosEngineeringTester,
    ConcurrentTester,
    EndToEndTester,
    MemoryLeakDetector,
    PerformanceRegressionTester,
    PropertyBasedTester,
    TestDataFactory,
    TestEnvironmentManager,
    TestReporter,
    TestMetrics,
    TestReport,
    create_advanced_test_suite
)


@pytest.fixture
def app():
    """Create a test application."""
    return Application("Test App")


@pytest.fixture
def advanced_suite(app):
    """Create an advanced test suite."""
    return create_advanced_test_suite(app)


class TestPropertyBasedTester:
    """Test property-based testing functionality."""
    
    def test_property_tester_initialization(self, app):
        """Test PropertyBasedTester initialization."""
        tester = PropertyBasedTester(app)
        assert tester.app == app
        assert tester.test_data == []
    
    @given(st.text(min_size=1, max_size=10))
    @settings(max_examples=5)
    def test_string_properties(self, app, text):
        """Test string property-based testing."""
        tester = PropertyBasedTester(app)
        tester.test_string_properties(text)
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=5)
    def test_numeric_properties(self, app, number):
        """Test numeric property-based testing."""
        tester = PropertyBasedTester(app)
        tester.test_numeric_properties(number)
    
    @given(st.lists(st.text(), min_size=1, max_size=5))
    @settings(max_examples=5)
    def test_list_properties(self, app, items):
        """Test list property-based testing."""
        tester = PropertyBasedTester(app)
        tester.test_list_properties(items)


class TestMutationTester:
    """Test mutation testing functionality."""
    
    def test_mutation_tester_initialization(self, app):
        """Test MutationTester initialization."""
        tester = MutationTester(app)
        assert tester.app == app
        assert tester.mutations == []
        assert tester.original_code == {}
    
    def test_create_mutation_arithmetic(self, app):
        """Test arithmetic mutation creation."""
        tester = MutationTester(app)
        
        def test_function(x, y):
            return x + y
        
        mutated_code = tester.create_mutation(test_function, "arithmetic")
        assert mutated_code is not None
        assert "x + y" not in mutated_code or "x - y" in mutated_code
    
    def test_create_mutation_comparison(self, app):
        """Test comparison mutation creation."""
        tester = MutationTester(app)
        
        def test_function(x, y):
            return x == y
        
        mutated_code = tester.create_mutation(test_function, "comparison")
        assert mutated_code is not None
    
    def test_mutation_killing(self, app):
        """Test mutation killing detection."""
        tester = MutationTester(app)
        
        def target_function(x):
            return x * 2
        
        def test_function():
            assert target_function(2) == 4
        
        test_suite = [test_function]
        results = tester.test_mutation_killing(test_suite, target_function)
        
        assert len(results) > 0
        for result in results:
            assert 'mutation_type' in result
            assert 'killed' in result
            assert 'mutated_code' in result


class TestChaosEngineeringTester:
    """Test chaos engineering functionality."""
    
    @pytest.mark.asyncio
    async def test_chaos_tester_initialization(self, app):
        """Test ChaosEngineeringTester initialization."""
        tester = ChaosEngineeringTester(app)
        assert tester.app == app
        assert tester.chaos_scenarios == []
    
    @pytest.mark.asyncio
    async def test_network_partition(self, app):
        """Test network partition simulation."""
        tester = ChaosEngineeringTester(app)
        
        async with tester.network_partition(duration=0.1):
            # Test that we can work during network partition
            await asyncio.sleep(0.05)
    
    @pytest.mark.asyncio
    async def test_high_latency(self, app):
        """Test high latency simulation."""
        tester = ChaosEngineeringTester(app)
        
        start_time = time.time()
        async with tester.high_latency(latency=0.1):
            await asyncio.sleep(0.01)
        end_time = time.time()
        
        # Should have added some latency
        assert end_time - start_time >= 0.1
    
    @pytest.mark.asyncio
    async def test_memory_pressure(self, app):
        """Test memory pressure simulation."""
        tester = ChaosEngineeringTester(app)
        
        async with tester.memory_pressure(pressure_level=0.1):
            # Test that we can work under memory pressure
            await asyncio.sleep(0.01)
    
    @pytest.mark.asyncio
    async def test_cpu_pressure(self, app):
        """Test CPU pressure simulation."""
        tester = ChaosEngineeringTester(app)
        
        async with tester.cpu_pressure(pressure_level=0.1):
            # Test that we can work under CPU pressure
            await asyncio.sleep(0.01)
    
    @pytest.mark.asyncio
    async def test_run_chaos_scenario(self, app):
        """Test running chaos scenarios."""
        tester = ChaosEngineeringTester(app)
        
        async def test_scenario():
            await asyncio.sleep(0.01)
            return True
        
        success = await tester.run_chaos_scenario("test_scenario", test_scenario)
        assert success is True
        assert len(tester.chaos_scenarios) == 1
        assert tester.chaos_scenarios[0]['name'] == "test_scenario"


class TestEndToEndTester:
    """Test end-to-end testing functionality."""
    
    @pytest.mark.asyncio
    async def test_e2e_tester_initialization(self, app):
        """Test EndToEndTester initialization."""
        tester = EndToEndTester(app)
        assert tester.app == app
        assert tester.test_scenarios == []
    
    @pytest.mark.asyncio
    async def test_user_journey_api_steps(self, app):
        """Test user journey with API steps."""
        tester = EndToEndTester(app)
        
        # Add a test route to the app
        @app.get("/test")
        async def test_route():
            return {"status": "ok"}
        
        steps = [
            {
                "name": "test_api_call",
                "type": "api_call",
                "data": {
                    "method": "GET",
                    "path": "/test",
                    "expected_status": 200
                }
            }
        ]
        
        success = await tester.test_user_journey("test_journey", steps)
        assert success is True
        assert len(tester.test_scenarios) == 1
    
    @pytest.mark.asyncio
    async def test_user_journey_assertion_steps(self, app):
        """Test user journey with assertion steps."""
        tester = EndToEndTester(app)
        
        steps = [
            {
                "name": "test_assertion",
                "type": "assertion",
                "data": {
                    "type": "api_response",
                    "actual": {"status": "ok"},
                    "expected": {"status": "ok"}
                }
            }
        ]
        
        success = await tester.test_user_journey("test_assertion_journey", steps)
        assert success is True


class TestPerformanceRegressionTester:
    """Test performance regression testing functionality."""
    
    def test_performance_tester_initialization(self, app):
        """Test PerformanceRegressionTester initialization."""
        tester = PerformanceRegressionTester(app)
        assert tester.app == app
        assert tester.baseline_metrics == {}
        assert tester.regression_threshold == 0.2
    
    def test_measure_performance(self, app):
        """Test performance measurement."""
        tester = PerformanceRegressionTester(app)
        
        with tester.measure_performance("test_function"):
            time.sleep(0.01)  # Simulate some work
    
    def test_set_and_save_baseline(self, app):
        """Test setting and saving baseline metrics."""
        tester = PerformanceRegressionTester(app)
        
        metrics = TestMetrics(
            execution_time=0.1,
            memory_usage=1024,
            cpu_usage=25.0,
            request_count=10,
            error_count=0
        )
        
        tester.set_baseline("test_function", metrics)
        assert "test_function" in tester.baseline_metrics
        
        # Test saving baseline
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            baseline_file = f.name
        
        try:
            tester.save_baseline(baseline_file)
            
            # Test loading baseline
            new_tester = PerformanceRegressionTester(app)
            new_tester.load_baseline(baseline_file)
            assert "test_function" in new_tester.baseline_metrics
        finally:
            Path(baseline_file).unlink(missing_ok=True)


class TestMemoryLeakDetector:
    """Test memory leak detection functionality."""
    
    def test_memory_detector_initialization(self):
        """Test MemoryLeakDetector initialization."""
        detector = MemoryLeakDetector()
        assert detector.snapshots == []
        assert detector.leak_threshold == 0.1
    
    def test_detect_leaks(self):
        """Test memory leak detection."""
        detector = MemoryLeakDetector()
        
        with detector.detect_leaks("test_function"):
            # Simulate some memory allocation
            data = [i for i in range(1000)]
        
        assert len(detector.snapshots) == 1
        snapshot = detector.snapshots[0]
        assert snapshot['test_name'] == "test_function"


class TestConcurrentTester:
    """Test concurrent testing functionality."""
    
    @pytest.mark.asyncio
    async def test_concurrent_tester_initialization(self, app):
        """Test ConcurrentTester initialization."""
        tester = ConcurrentTester(app)
        assert tester.app == app
        assert tester.concurrent_results == []
    
    @pytest.mark.asyncio
    async def test_run_concurrent_requests(self, app):
        """Test running concurrent requests."""
        tester = ConcurrentTester(app)
        
        async def test_request():
            await asyncio.sleep(0.01)
            return {"status": "success"}
        
        results = await tester.run_concurrent_requests(
            test_request,
            concurrency=2,
            total_requests=4
        )
        
        assert 'success_rate' in results
        assert 'avg_duration' in results
        assert 'requests_per_second' in results
        assert len(tester.concurrent_results) == 1


class TestTestDataFactory:
    """Test test data factory functionality."""
    
    def test_data_factory_initialization(self):
        """Test TestDataFactory initialization."""
        factory = TestDataFactory()
        assert factory.factories == {}
        assert factory.sequences == {}
    
    def test_register_and_create_factory(self):
        """Test registering and using factories."""
        factory = TestDataFactory()
        
        class TestModel:
            def __init__(self, id, name):
                self.id = id
                self.name = name
        
        def create_test_model(**kwargs):
            return TestModel(
                id=kwargs.get('id', 1),
                name=kwargs.get('name', 'test')
            )
        
        factory.register_factory(TestModel, create_test_model)
        
        # Test creating single instance
        instance = factory.create(TestModel, id=5, name="custom")
        assert instance.id == 5
        assert instance.name == "custom"
        
        # Test creating batch
        instances = factory.create_batch(TestModel, 3)
        assert len(instances) == 3
        assert all(isinstance(inst, TestModel) for inst in instances)
    
    def test_sequence_generation(self):
        """Test sequence generation."""
        factory = TestDataFactory()
        
        # Test first sequence
        assert factory.sequence("test_seq") == 1
        assert factory.sequence("test_seq") == 2
        assert factory.sequence("test_seq") == 3
        
        # Test different sequence
        assert factory.sequence("other_seq") == 1
        assert factory.sequence("other_seq") == 2


class TestTestEnvironmentManager:
    """Test test environment management functionality."""
    
    def test_env_manager_initialization(self):
        """Test TestEnvironmentManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_manager = TestEnvironmentManager(temp_dir)
            assert env_manager.base_dir == Path(temp_dir)
            assert env_manager.environments == {}
    
    def test_isolated_environment(self):
        """Test isolated environment creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_manager = TestEnvironmentManager(temp_dir)
            
            with env_manager.isolated_environment("test_env"):
                # Test that environment variables are set
                import os
                assert os.environ.get('TEST_ENV') == "test_env"
                assert os.environ.get('TEST_DIR') is not None
    
    def test_cleanup_environment(self):
        """Test environment cleanup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_manager = TestEnvironmentManager(temp_dir)
            
            # Create an environment
            env_dir = Path(temp_dir) / "test_env"
            env_dir.mkdir()
            test_file = env_dir / "test.txt"
            test_file.write_text("test")
            
            # Clean up
            env_manager.cleanup_environment("test_env")
            assert not env_dir.exists()


class TestTestReporter:
    """Test test reporting functionality."""
    
    def test_reporter_initialization(self):
        """Test TestReporter initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = TestReporter(temp_dir)
            assert reporter.output_dir == Path(temp_dir)
            assert reporter.reports == []
    
    def test_add_report_and_generate_summary(self):
        """Test adding reports and generating summary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = TestReporter(temp_dir)
            
            # Create test metrics
            metrics = TestMetrics(
                execution_time=0.1,
                memory_usage=1024,
                cpu_usage=25.0,
                request_count=10,
                error_count=0
            )
            
            # Create test report
            report = TestReport(
                test_name="test_function",
                status="passed",
                metrics=metrics,
                errors=[],
                warnings=[],
                performance_regression=False,
                memory_leak_detected=False
            )
            
            reporter.add_report(report)
            assert len(reporter.reports) == 1
            
            # Generate summary
            summary = reporter.generate_summary()
            assert summary['total_tests'] == 1
            assert summary['passed_tests'] == 1
            assert summary['failed_tests'] == 0
            assert summary['success_rate'] == 1.0
    
    def test_save_reports(self):
        """Test saving reports to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = TestReporter(temp_dir)
            
            # Add a test report
            metrics = TestMetrics(
                execution_time=0.1,
                memory_usage=1024,
                cpu_usage=25.0,
                request_count=10,
                error_count=0
            )
            
            report = TestReport(
                test_name="test_function",
                status="passed",
                metrics=metrics
            )
            
            reporter.add_report(report)
            
            # Save reports
            output_file = reporter.save_reports("test_report.json")
            assert output_file.exists()
            
            # Verify content
            with open(output_file, 'r') as f:
                data = json.load(f)
                assert 'summary' in data
                assert 'reports' in data
                assert len(data['reports']) == 1
    
    def test_generate_html_report(self):
        """Test HTML report generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = TestReporter(temp_dir)
            
            # Add a test report
            metrics = TestMetrics(
                execution_time=0.1,
                memory_usage=1024,
                cpu_usage=25.0,
                request_count=10,
                error_count=0
            )
            
            report = TestReport(
                test_name="test_function",
                status="passed",
                metrics=metrics
            )
            
            reporter.add_report(report)
            
            # Generate HTML report
            output_file = reporter.generate_html_report("test_report.html")
            assert output_file.exists()
            
            # Verify content
            with open(output_file, 'r') as f:
                content = f.read()
                assert "QakeAPI Test Report" in content
                assert "test_function" in content


class TestAdvancedTestSuite:
    """Test the complete advanced test suite."""
    
    def test_create_advanced_test_suite(self, app):
        """Test creating a complete advanced test suite."""
        suite = create_advanced_test_suite(app)
        
        # Check that all components are present
        assert 'property_tester' in suite
        assert 'mutation_tester' in suite
        assert 'chaos_tester' in suite
        assert 'e2e_tester' in suite
        assert 'performance_tester' in suite
        assert 'memory_detector' in suite
        assert 'concurrent_tester' in suite
        assert 'data_factory' in suite
        assert 'env_manager' in suite
        assert 'reporter' in suite
        
        # Check that components are of correct types
        assert isinstance(suite['property_tester'], PropertyBasedTester)
        assert isinstance(suite['mutation_tester'], MutationTester)
        assert isinstance(suite['chaos_tester'], ChaosEngineeringTester)
        assert isinstance(suite['e2e_tester'], EndToEndTester)
        assert isinstance(suite['performance_tester'], PerformanceRegressionTester)
        assert isinstance(suite['memory_detector'], MemoryLeakDetector)
        assert isinstance(suite['concurrent_tester'], ConcurrentTester)
        assert isinstance(suite['data_factory'], TestDataFactory)
        assert isinstance(suite['env_manager'], TestEnvironmentManager)
        assert isinstance(suite['reporter'], TestReporter)
    
    @pytest.mark.asyncio
    async def test_integration_workflow(self, app):
        """Test integration workflow with multiple components."""
        suite = create_advanced_test_suite(app)
        
        # Test data factory
        factory = suite['data_factory']
        
        class TestUser:
            def __init__(self, id, name):
                self.id = id
                self.name = name
        
        def create_user(**kwargs):
            return TestUser(
                id=kwargs.get('id', factory.sequence('user_id')),
                name=kwargs.get('name', f"User{factory.sequence('user_name')}")
            )
        
        factory.register_factory(TestUser, create_user)
        users = factory.create_batch(TestUser, 3)
        assert len(users) == 3
        
        # Test performance measurement
        performance_tester = suite['performance_tester']
        with performance_tester.measure_performance("integration_test"):
            await asyncio.sleep(0.01)
        
        # Test memory leak detection
        memory_detector = suite['memory_detector']
        with memory_detector.detect_leaks("integration_test"):
            data = [i for i in range(100)]
        
        # Test concurrent requests
        concurrent_tester = suite['concurrent_tester']
        async def test_request():
            await asyncio.sleep(0.01)
            return {"status": "success"}
        
        results = await concurrent_tester.run_concurrent_requests(
            test_request,
            concurrency=2,
            total_requests=4
        )
        assert 'success_rate' in results
        
        # Test reporting
        reporter = suite['reporter']
        metrics = TestMetrics(
            execution_time=0.1,
            memory_usage=1024,
            cpu_usage=25.0,
            request_count=10,
            error_count=0
        )
        
        report = TestReport(
            test_name="integration_test",
            status="passed",
            metrics=metrics
        )
        
        reporter.add_report(report)
        summary = reporter.generate_summary()
        assert summary['total_tests'] == 1
        assert summary['passed_tests'] == 1


# Pytest fixtures for advanced testing
@pytest.fixture
def advanced_test_suite(app):
    """Pytest fixture for advanced testing."""
    return create_advanced_test_suite(app)


@pytest.fixture
def sample_test_metrics():
    """Sample test metrics for testing."""
    return TestMetrics(
        execution_time=0.1,
        memory_usage=1024,
        cpu_usage=25.0,
        request_count=10,
        error_count=0
    )


@pytest.fixture
def sample_test_report(sample_test_metrics):
    """Sample test report for testing."""
    return TestReport(
        test_name="sample_test",
        status="passed",
        metrics=sample_test_metrics,
        errors=[],
        warnings=[],
        performance_regression=False,
        memory_leak_detected=False
    ) 