Advanced Testing
================

QakeAPI provides a comprehensive advanced testing framework that goes beyond traditional unit and integration testing. This framework includes property-based testing, mutation testing, chaos engineering, performance regression testing, and more.

Overview
--------

The advanced testing framework is designed to help developers create more robust and reliable applications by:

- **Property-based testing**: Testing properties that should always hold true
- **Mutation testing**: Ensuring test quality by introducing code mutations
- **Chaos engineering**: Testing system resilience under failure conditions
- **Performance regression testing**: Detecting performance degradations
- **Memory leak detection**: Identifying memory leaks early
- **Concurrent testing**: Testing system behavior under concurrent load
- **Test data factories**: Generating realistic test data
- **Test environment management**: Isolating test environments
- **Comprehensive reporting**: Detailed test reports and analytics

Installation
------------

The advanced testing framework requires additional dependencies:

.. code-block:: bash

    pip install hypothesis psutil memory-profiler

Basic Usage
-----------

Create an advanced test suite:

.. code-block:: python

    from qakeapi import Application
    from qakeapi.testing.advanced import create_advanced_test_suite

    app = Application("My App")
    test_suite = create_advanced_test_suite(app)

Property-Based Testing
----------------------

Property-based testing uses Hypothesis to generate test data and verify that certain properties always hold true.

.. code-block:: python

    from qakeapi.testing.advanced import PropertyBasedTester
    from hypothesis import given, settings, strategies as st

    tester = PropertyBasedTester(app)

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_string_properties(text):
        # Test that string operations are consistent
        assert len(text) >= 1
        assert len(text) <= 100
        assert text == text.strip() or text != text.strip()

    @given(st.integers(min_value=1, max_value=1000))
    @settings(max_examples=50)
    def test_numeric_properties(number):
        # Test that numeric operations are consistent
        assert number >= 1
        assert number <= 1000
        assert number * 2 == number + number
        assert number + 0 == number

Mutation Testing
----------------

Mutation testing introduces small changes to your code and verifies that your tests can detect these changes.

.. code-block:: python

    from qakeapi.testing.advanced import MutationTester

    tester = MutationTester(app)

    def target_function(x):
        return x * 2

    def test_function():
        assert target_function(2) == 4

    # Test if mutations are killed by the test suite
    results = tester.test_mutation_killing([test_function], target_function)
    
    for result in results:
        print(f"Mutation type: {result['mutation_type']}")
        print(f"Killed: {result['killed']}")

Chaos Engineering
-----------------

Chaos engineering simulates real-world failure scenarios to test system resilience.

.. code-block:: python

    from qakeapi.testing.advanced import ChaosEngineeringTester

    tester = ChaosEngineeringTester(app)

    # Simulate network partition
    async with tester.network_partition(duration=1.0):
        # Make requests during network partition
        response = await client.get("/api/data")
        assert response.status_code in [200, 503]

    # Simulate high latency
    async with tester.high_latency(latency=2.0):
        # Test timeout handling
        response = await client.get("/api/data", timeout=1.0)
        assert response.status_code == 408

    # Simulate memory pressure
    async with tester.memory_pressure(pressure_level=0.8):
        # Test memory management
        response = await client.get("/api/data")
        assert response.status_code == 200

    # Simulate CPU pressure
    async with tester.cpu_pressure(pressure_level=0.8):
        # Test CPU-intensive operations
        response = await client.get("/api/compute")
        assert response.status_code == 200

End-to-End Testing
------------------

End-to-end testing simulates complete user journeys across multiple endpoints.

.. code-block:: python

    from qakeapi.testing.advanced import EndToEndTester

    tester = EndToEndTester(app)

    # Define a user journey
    steps = [
        {
            "name": "create_user",
            "type": "api_call",
            "data": {
                "method": "POST",
                "path": "/users",
                "payload": {"name": "John", "email": "john@example.com"},
                "expected_status": 200
            }
        },
        {
            "name": "create_product",
            "type": "api_call",
            "data": {
                "method": "POST",
                "path": "/products",
                "payload": {"name": "Product", "price": 10.0},
                "expected_status": 200
            }
        },
        {
            "name": "create_order",
            "type": "api_call",
            "data": {
                "method": "POST",
                "path": "/orders",
                "payload": {"user_id": 1, "product_id": 1},
                "expected_status": 200
            }
        }
    ]

    # Run the user journey
    success = await tester.test_user_journey("complete_order_flow", steps)
    assert success is True

Performance Regression Testing
------------------------------

Performance regression testing helps detect when code changes cause performance degradations.

.. code-block:: python

    from qakeapi.testing.advanced import PerformanceRegressionTester

    tester = PerformanceRegressionTester(app)

    # Measure performance of a function
    with tester.measure_performance("api_endpoint"):
        response = await client.get("/api/data")
        assert response.status_code == 200

    # Set baseline metrics
    metrics = TestMetrics(
        execution_time=0.1,
        memory_usage=1024,
        cpu_usage=25.0,
        request_count=10,
        error_count=0
    )
    tester.set_baseline("api_endpoint", metrics)

    # Save baseline to file
    tester.save_baseline("baseline.json")

    # Load baseline from file
    tester.load_baseline("baseline.json")

Memory Leak Detection
---------------------

Memory leak detection helps identify memory leaks early in development.

.. code-block:: python

    from qakeapi.testing.advanced import MemoryLeakDetector

    detector = MemoryLeakDetector()

    # Test for memory leaks
    with detector.detect_leaks("memory_intensive_function"):
        # Simulate potential memory leak
        data = []
        for i in range(1000):
            data.append({
                "id": i,
                "large_string": "x" * 1000,
                "timestamp": time.time()
            })
        
        # Clean up to prevent leak
        data.clear()

    # Check snapshots for memory issues
    for snapshot in detector.snapshots:
        if snapshot['memory_increase'] > detector.leak_threshold:
            print(f"Potential memory leak in {snapshot['test_name']}")

Concurrent Testing
------------------

Concurrent testing verifies system behavior under concurrent load.

.. code-block:: python

    from qakeapi.testing.advanced import ConcurrentTester

    tester = ConcurrentTester(app)

    # Define a test request function
    async def test_request():
        response = await client.get("/api/data")
        return {"status": "success" if response.status_code == 200 else "failed"}

    # Run concurrent requests
    results = await tester.run_concurrent_requests(
        test_request,
        concurrency=10,
        total_requests=100
    )

    print(f"Success rate: {results['success_rate']:.2%}")
    print(f"Average duration: {results['avg_duration']:.3f}s")
    print(f"Requests per second: {results['requests_per_second']:.1f}")

Test Data Factories
-------------------

Test data factories help generate realistic test data.

.. code-block:: python

    from qakeapi.testing.advanced import TestDataFactory

    factory = TestDataFactory()

    # Register a factory for a model
    class User:
        def __init__(self, id, name, email):
            self.id = id
            self.name = name
            self.email = email

    def create_user_factory(**kwargs):
        return User(
            id=kwargs.get('id', factory.sequence('user_id')),
            name=kwargs.get('name', f"User{factory.sequence('user_name')}"),
            email=kwargs.get('email', f"user{factory.sequence('user_email')}@example.com")
        )

    factory.register_factory(User, create_user_factory)

    # Create test data
    user = factory.create(User, name="John")
    users = factory.create_batch(User, 5)

    # Use sequences for unique values
    sequence_value = factory.sequence("test_sequence")

Test Environment Management
---------------------------

Test environment management provides isolated environments for testing.

.. code-block:: python

    from qakeapi.testing.advanced import TestEnvironmentManager

    env_manager = TestEnvironmentManager("test_env")

    # Create isolated test environment
    with env_manager.isolated_environment("test_env"):
        # Set environment variables
        import os
        os.environ['TEST_MODE'] = 'true'
        os.environ['DATABASE_URL'] = 'sqlite:///test.db'
        
        # Run tests in isolated environment
        # ...

    # Clean up environment
    env_manager.cleanup_environment("test_env")
    env_manager.cleanup_all()

Test Reporting
--------------

Comprehensive test reporting provides detailed analytics and insights.

.. code-block:: python

    from qakeapi.testing.advanced import TestReporter, TestMetrics, TestReport

    reporter = TestReporter("test_reports")

    # Create test metrics
    metrics = TestMetrics(
        execution_time=0.15,
        memory_usage=1024 * 1024,
        cpu_usage=25.5,
        request_count=100,
        error_count=2
    )

    # Create test report
    report = TestReport(
        test_name="api_performance_test",
        status="passed",
        metrics=metrics,
        errors=[],
        warnings=["High memory usage detected"],
        performance_regression=False,
        memory_leak_detected=False
    )

    reporter.add_report(report)

    # Generate reports
    summary = reporter.generate_summary()
    json_report = reporter.save_reports("test_report.json")
    html_report = reporter.generate_html_report("test_report.html")

Integration Example
-------------------

Here's a complete example showing how to use all advanced testing features together:

.. code-block:: python

    import asyncio
    from qakeapi import Application
    from qakeapi.testing.advanced import create_advanced_test_suite

    app = Application("Advanced Testing Example")

    @app.get("/")
    async def home():
        return {"message": "Advanced Testing Example"}

    @app.get("/api/data")
    async def get_data():
        return {"data": [1, 2, 3, 4, 5]}

    async def run_advanced_tests():
        # Create test suite
        suite = create_advanced_test_suite(app)
        
        # Property-based testing
        property_tester = suite['property_tester']
        property_tester.test_string_properties("test")
        property_tester.test_numeric_properties(42)
        
        # Chaos engineering
        chaos_tester = suite['chaos_tester']
        async with chaos_tester.network_partition(duration=0.5):
            # Test during network issues
            pass
        
        # Performance testing
        performance_tester = suite['performance_tester']
        with performance_tester.measure_performance("api_test"):
            # Test API performance
            pass
        
        # Memory leak detection
        memory_detector = suite['memory_detector']
        with memory_detector.detect_leaks("memory_test"):
            # Test for memory leaks
            pass
        
        # Concurrent testing
        concurrent_tester = suite['concurrent_tester']
        async def test_request():
            return {"status": "success"}
        
        results = await concurrent_tester.run_concurrent_requests(
            test_request,
            concurrency=5,
            total_requests=20
        )
        
        # Test data factory
        data_factory = suite['data_factory']
        # ... register factories and create test data
        
        # Test environment management
        env_manager = suite['env_manager']
        with env_manager.isolated_environment("test_env"):
            # Run tests in isolated environment
            pass
        
        # Test reporting
        reporter = suite['reporter']
        # ... add reports and generate summaries

    if __name__ == "__main__":
        asyncio.run(run_advanced_tests())

Best Practices
--------------

1. **Start with property-based testing**: Use property-based testing to verify fundamental properties of your code.

2. **Use mutation testing for test quality**: Ensure your tests are actually testing the right things.

3. **Implement chaos engineering gradually**: Start with simple scenarios and gradually increase complexity.

4. **Set performance baselines early**: Establish performance baselines early in development.

5. **Monitor memory usage**: Use memory leak detection regularly, especially for long-running applications.

6. **Test concurrency**: Always test your application under concurrent load.

7. **Use realistic test data**: Use test data factories to generate realistic test scenarios.

8. **Isolate test environments**: Use isolated environments to prevent test interference.

9. **Generate comprehensive reports**: Use detailed reporting to track test results over time.

10. **Automate everything**: Integrate advanced testing into your CI/CD pipeline.

Configuration
-------------

The advanced testing framework can be configured through environment variables:

- ``ADVANCED_TESTING_ENABLED``: Enable/disable advanced testing features
- ``MUTATION_TESTING_ENABLED``: Enable/disable mutation testing
- ``CHAOS_ENGINEERING_ENABLED``: Enable/disable chaos engineering
- ``PERFORMANCE_REGRESSION_THRESHOLD``: Set performance regression threshold
- ``MEMORY_LEAK_THRESHOLD``: Set memory leak detection threshold

.. code-block:: bash

    export ADVANCED_TESTING_ENABLED=true
    export MUTATION_TESTING_ENABLED=true
    export CHAOS_ENGINEERING_ENABLED=true
    export PERFORMANCE_REGRESSION_THRESHOLD=0.2
    export MEMORY_LEAK_THRESHOLD=0.1

Troubleshooting
---------------

Common issues and solutions:

1. **Hypothesis tests failing**: Reduce the number of examples or adjust the strategy
2. **Memory leak false positives**: Adjust the leak threshold or improve cleanup
3. **Performance tests flaky**: Increase the regression threshold or run more iterations
4. **Chaos engineering too aggressive**: Reduce the pressure levels or duration
5. **Concurrent tests timing out**: Reduce concurrency or increase timeouts

For more information, see the example application in ``examples_app/advanced_testing_app.py``. 