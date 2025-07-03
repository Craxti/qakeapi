"""
Advanced Testing Example Application

This application demonstrates advanced testing capabilities of QakeAPI:
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
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create application
app = Application("Advanced Testing Example")

# Sample data models
class User:
    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }

class Product:
    def __init__(self, id: int, name: str, price: float, category: str):
        self.id = id
        self.name = name
        self.price = price
        self.category = category
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'category': self.category
        }

# In-memory storage
users_db = {}
products_db = {}
orders_db = {}

# Initialize advanced testing suite
test_suite = create_advanced_test_suite(app)

# Routes for testing different scenarios
@app.get("/")
async def home():
    """Home page with testing information."""
    return {
        "message": "Advanced Testing Example",
        "version": "1.0.3",
        "features": [
            "Property-based testing",
            "Mutation testing", 
            "Chaos engineering",
            "End-to-end testing",
            "Performance regression testing",
            "Memory leak detection",
            "Concurrent testing",
            "Test data factories",
            "Test environment management",
            "Test reporting"
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
async def get_users():
    """Get all users - for property-based testing."""
    return {"users": list(users_db.values())}

@app.post("/users")
async def create_user(user_data: Dict):
    """Create a user - for mutation testing."""
    user_id = len(users_db) + 1
    user = User(user_id, user_data["name"], user_data["email"])
    users_db[user_id] = user
    return user.to_dict()

@app.get("/products")
async def get_products():
    """Get all products - for chaos engineering tests."""
    return {"products": list(products_db.values())}

@app.post("/products")
async def create_product(product_data: Dict):
    """Create a product - for performance testing."""
    product_id = len(products_db) + 1
    product = Product(
        product_id,
        product_data["name"],
        product_data["price"],
        product_data["category"]
    )
    products_db[product_id] = product
    return product.to_dict()

@app.get("/orders")
async def get_orders():
    """Get all orders - for concurrent testing."""
    return {"orders": list(orders_db.values())}

@app.post("/orders")
async def create_order(order_data: Dict):
    """Create an order - for memory leak detection."""
    order_id = len(orders_db) + 1
    order = {
        "id": order_id,
        "user_id": order_data["user_id"],
        "product_id": order_data["product_id"],
        "quantity": order_data["quantity"],
        "total": order_data["total"],
        "created_at": time.time()
    }
    orders_db[order_id] = order
    return order

@app.get("/performance")
async def performance_test():
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
async def chaos_test():
    """Chaos engineering test endpoint."""
    # Simulate potential failure scenarios
    import random
    
    # Randomly fail
    if random.random() < 0.1:  # 10% chance of failure
        raise Exception("Chaos test failure")
    
    # Simulate slow response
    if random.random() < 0.2:  # 20% chance of slow response
        await asyncio.sleep(random.uniform(0.5, 2.0))
    
    return {"status": "chaos_test_passed", "timestamp": time.time()}

@app.get("/concurrent")
async def concurrent_test():
    """Concurrent testing endpoint."""
    # Simulate concurrent processing
    await asyncio.sleep(0.05)
    
    return {
        "status": "concurrent_test_passed",
        "timestamp": time.time(),
        "thread_id": id(asyncio.current_task())
    }

@app.get("/memory")
async def memory_test():
    """Memory leak detection test endpoint."""
    # Simulate memory allocation
    data = []
    for i in range(1000):
        data.append({
            "id": i,
            "large_string": "x" * 1000,
            "timestamp": time.time()
        })
    
    return {
        "status": "memory_test_passed",
        "data_size": len(data),
        "timestamp": time.time()
    }

@app.get("/test-report")
async def test_report():
    """Generate and return test report."""
    # Create sample test reports
    reporter = test_suite['reporter']
    
    # Sample test metrics
    metrics = TestMetrics(
        execution_time=0.15,
        memory_usage=1024 * 1024,  # 1MB
        cpu_usage=25.5,
        request_count=100,
        error_count=2
    )
    
    # Sample test report
    report = TestReport(
        test_name="advanced_testing_example",
        status="passed",
        metrics=metrics,
        errors=[],
        warnings=["High memory usage detected"],
        performance_regression=False,
        memory_leak_detected=False
    )
    
    reporter.add_report(report)
    
    # Generate summary
    summary = reporter.generate_summary()
    
    return {
        "test_report": summary,
        "timestamp": time.time()
    }

# Advanced testing demonstration functions
async def demonstrate_property_based_testing():
    """Demonstrate property-based testing."""
    logger.info("Running property-based testing demonstration...")
    
    property_tester = test_suite['property_tester']
    
    # Test string properties
    property_tester.test_string_properties("test_string")
    
    # Test numeric properties  
    property_tester.test_numeric_properties(42)
    
    # Test list properties
    property_tester.test_list_properties(["item1", "item2", "item3"])
    
    logger.info("Property-based testing demonstration completed")

async def demonstrate_chaos_engineering():
    """Demonstrate chaos engineering."""
    logger.info("Running chaos engineering demonstration...")
    
    chaos_tester = test_suite['chaos_tester']
    
    # Network partition scenario
    async with chaos_tester.network_partition(duration=0.5):
        # Make requests during network partition
        pass
    
    # High latency scenario
    async with chaos_tester.high_latency(latency=1.0):
        # Make requests during high latency
        pass
    
    # Memory pressure scenario
    async with chaos_tester.memory_pressure(pressure_level=0.5):
        # Make requests during memory pressure
        pass
    
    logger.info("Chaos engineering demonstration completed")

async def demonstrate_concurrent_testing():
    """Demonstrate concurrent testing."""
    logger.info("Running concurrent testing demonstration...")
    
    concurrent_tester = test_suite['concurrent_tester']
    
    # Define a test request function
    async def test_request():
        await asyncio.sleep(0.01)  # Simulate request processing
        return {"status": "success"}
    
    # Run concurrent requests
    results = await concurrent_tester.run_concurrent_requests(
        test_request,
        concurrency=5,
        total_requests=20
    )
    
    logger.info(f"Concurrent testing results: {results}")
    logger.info("Concurrent testing demonstration completed")

async def demonstrate_performance_testing():
    """Demonstrate performance testing."""
    logger.info("Running performance testing demonstration...")
    
    performance_tester = test_suite['performance_tester']
    
    # Measure performance of a function
    with performance_tester.measure_performance("demo_function"):
        # Simulate some work
        await asyncio.sleep(0.1)
        data = [i * 2 for i in range(1000)]
        _ = sum(data)
    
    logger.info("Performance testing demonstration completed")

async def demonstrate_memory_leak_detection():
    """Demonstrate memory leak detection."""
    logger.info("Running memory leak detection demonstration...")
    
    memory_detector = test_suite['memory_detector']
    
    # Test for memory leaks
    with memory_detector.detect_leaks("demo_memory_test"):
        # Simulate potential memory leak
        data = []
        for i in range(1000):
            data.append({
                "id": i,
                "large_string": "x" * 1000,
                "timestamp": time.time()
            })
        
        # Clean up (or don't to simulate leak)
        # data.clear()  # Uncomment to prevent leak
    
    logger.info("Memory leak detection demonstration completed")

async def demonstrate_test_data_factory():
    """Demonstrate test data factory."""
    logger.info("Running test data factory demonstration...")
    
    data_factory = test_suite['data_factory']
    
    # Register factories
    def create_user_factory(**kwargs):
        return User(
            id=kwargs.get('id', data_factory.sequence('user_id')),
            name=kwargs.get('name', f"User{data_factory.sequence('user_name')}"),
            email=kwargs.get('email', f"user{data_factory.sequence('user_email')}@example.com")
        )
    
    def create_product_factory(**kwargs):
        return Product(
            id=kwargs.get('id', data_factory.sequence('product_id')),
            name=kwargs.get('name', f"Product{data_factory.sequence('product_name')}"),
            price=kwargs.get('price', 10.0),
            category=kwargs.get('category', 'electronics')
        )
    
    data_factory.register_factory(User, create_user_factory)
    data_factory.register_factory(Product, create_product_factory)
    
    # Create test data
    users = data_factory.create_batch(User, 5)
    products = data_factory.create_batch(Product, 3)
    
    logger.info(f"Created {len(users)} users and {len(products)} products")
    logger.info("Test data factory demonstration completed")

async def demonstrate_test_environment_management():
    """Demonstrate test environment management."""
    logger.info("Running test environment management demonstration...")
    
    env_manager = test_suite['env_manager']
    
    # Create isolated test environment
    with env_manager.isolated_environment("demo_test_env"):
        # Work in isolated environment
        logger.info("Working in isolated test environment")
        
        # Create some test files
        test_file = Path("test_file.txt")
        test_file.write_text("Test data")
        
        # Verify file exists
        assert test_file.exists()
    
    # Environment is automatically cleaned up
    logger.info("Test environment management demonstration completed")

async def demonstrate_test_reporting():
    """Demonstrate test reporting."""
    logger.info("Running test reporting demonstration...")
    
    reporter = test_suite['reporter']
    
    # Create sample test reports
    for i in range(5):
        metrics = TestMetrics(
            execution_time=0.1 + i * 0.05,
            memory_usage=1024 * 1024 + i * 1000,
            cpu_usage=20.0 + i * 2.0,
            request_count=10 + i * 5,
            error_count=i if i < 2 else 0
        )
        
        report = TestReport(
            test_name=f"test_{i}",
            status="passed" if i < 4 else "failed",
            metrics=metrics,
            errors=[] if i < 4 else ["Test failed"],
            warnings=[] if i < 3 else ["Performance warning"],
            performance_regression=i == 3,
            memory_leak_detected=i == 4
        )
        
        reporter.add_report(report)
    
    # Generate reports
    json_report = reporter.save_reports("demo_test_report.json")
    html_report = reporter.generate_html_report("demo_test_report.html")
    
    logger.info(f"Test reports generated: {json_report}, {html_report}")
    logger.info("Test reporting demonstration completed")

async def run_all_demonstrations():
    """Run all advanced testing demonstrations."""
    logger.info("Starting advanced testing demonstrations...")
    
    demonstrations = [
        demonstrate_property_based_testing,
        demonstrate_chaos_engineering,
        demonstrate_concurrent_testing,
        demonstrate_performance_testing,
        demonstrate_memory_leak_detection,
        demonstrate_test_data_factory,
        demonstrate_test_environment_management,
        demonstrate_test_reporting
    ]
    
    for demo in demonstrations:
        try:
            await demo()
        except Exception as e:
            logger.error(f"Demonstration failed: {e}")
    
    logger.info("All advanced testing demonstrations completed")

# Background task to run demonstrations
@app.background_tasks
async def run_demonstrations_task():
    """Background task to run testing demonstrations."""
    await run_all_demonstrations()

if __name__ == "__main__":
    import uvicorn
    
    # Start demonstrations in background
    asyncio.create_task(run_demonstrations_task())
    
    # Run the application
    uvicorn.run(app, host="0.0.0.0", port=8018) 