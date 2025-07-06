"""
Example of using the enhanced testing system in QakeAPI.
"""
import asyncio
import tempfile
from pathlib import Path

from qakeapi import Application
from qakeapi.testing.fixtures import (
    FixtureFactory,
    TestFixtures,
    with_fixtures,
    user_fixture,
    post_fixture
)
from qakeapi.testing.database import (
    TestDatabase,
    DatabaseTestUtils,
    with_database,
    test_database
)
from qakeapi.testing.mocks import (
    MockService,
    MockExternalAPI,
    MockResponse,
    with_mock_service,
    create_user_service
)
from qakeapi.testing.performance import (
    PerformanceTester,
    BenchmarkSuite,
    benchmark,
    stress_test
)
from qakeapi.testing.load_testing import (
    LoadTester,
    LoadTestConfig,
    create_simple_load_test
)

# Create application for testing
app = Application(title="Enhanced Testing Example", version="1.0.3")

@app.get("/users")
async def get_users(request):
    """Get list of users."""
    return {"users": [
        {"id": 1, "name": "John Doe", "email": "john@example.com"},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
    ]}

@app.get("/")
async def home(request):
    """Home page."""
    return {
        "message": "Enhanced Testing Example API",
        "version": "1.0.0",
        "endpoints": {
            "users": "/users",
            "user_by_id": "/users/{id}",
            "posts": "/posts"
        }
    }

@app.get("/users/{user_id}")
async def get_user(request):
    """Get user by ID."""
    # Extract user_id from path parameters
    user_id = int(request.path_params.get("user_id", 0))
    
    users = {
        1: {"id": 1, "name": "John Doe", "email": "john@example.com"},
        2: {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
    }
    
    if user_id not in users:
        return {"error": "User not found"}, 404
    
    return users[user_id]

@app.post("/users")
async def create_user(request):
    """Create new user."""
    data = await request.json()
    return {"id": 3, "name": data.get("name"), "email": data.get("email")}

@app.get("/posts")
async def get_posts(request):
    """Get list of posts."""
    return {"posts": [
        {"id": 1, "title": "First Post", "content": "Hello World"},
        {"id": 2, "title": "Second Post", "content": "Another post"}
    ]}


# Examples of using fixtures
def demonstrate_fixtures():
    """Demonstration of working with fixtures."""
    print("\n=== FIXTURES DEMONSTRATION ===")
    
    # Create fixture factory
    factory = FixtureFactory()
    
    # Generate test data
    user = user_fixture(factory)
    post = post_fixture(factory)
    
    print(f"Generated user: {user}")
    print(f"Generated post: {post}")
    
    # Create fixture manager
    fixtures = TestFixtures()
    
    # Register custom fixtures
    def custom_user_factory():
        return {"id": 999, "name": "Custom User", "email": "custom@example.com"}
    
    fixtures.register_fixture("custom_user", custom_user_factory)
    
    # Get fixture
    custom_user = fixtures.get_fixture("custom_user")
    print(f"Custom fixture: {custom_user}")


# Examples of using database
async def demonstrate_database():
    """Demonstration of working with test database."""
    print("\n=== DATABASE DEMONSTRATION ===")
    
    # Create test database
    db = TestDatabase()
    await db.setup()
    
    # Create tables
    db.execute_script("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        );
        
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            author_id INTEGER,
            FOREIGN KEY (author_id) REFERENCES users (id)
        );
    """)
    
    # Insert data
    user_id = db.insert("users", {"name": "Test User", "email": "test@example.com"})
    post_id = db.insert("posts", {
        "title": "Test Post",
        "content": "This is a test post",
        "author_id": user_id
    })
    
    # Get data
    user = db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    post = db.fetch_one("SELECT * FROM posts WHERE id = ?", (post_id,))
    
    print(f"User: {user}")
    print(f"Post: {post}")
    
    # Update data
    db.update("users", {"name": "Updated User"}, "id = ?", (user_id,))
    updated_user = db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    print(f"Updated user: {updated_user}")
    
    await db.teardown()


# Examples of using mocks
async def demonstrate_mocks():
    """Demonstration of working with mocks."""
    print("\n=== MOCKS DEMONSTRATION ===")
    
    # Create mock service
    user_service = MockService("users")
    
    # Add responses
    user_service.add_response("GET", "/users", MockResponse(
        status=200,
        body={"users": [{"id": 1, "name": "Mock User"}]}
    ))
    
    user_service.add_response("POST", "/users", MockResponse(
        status=201,
        body={"id": 2, "name": "New User"}
    ))
    
    # Create mock API
    mock_api = MockExternalAPI()
    mock_api.add_service(user_service)
    
    # Start mock server
    await mock_api.start(port=8080)
    
    try:
        # Simulate calls
        user_service.record_call("GET", "/users", {"Accept": "application/json"}, {})
        user_service.record_call("POST", "/users", {"Content-Type": "application/json"}, {"name": "New User"})
        
        # Get call history
        call_history = user_service.get_call_history()
        print(f"Call history: {call_history}")
        
        # Get call count
        get_calls = user_service.get_call_count("GET")
        post_calls = user_service.get_call_count("POST")
        print(f"GET calls: {get_calls}, POST calls: {post_calls}")
        
    finally:
        await mock_api.stop()


# Performance testing examples
async def demonstrate_performance():
    """Demonstration of performance testing."""
    print("\n=== PERFORMANCE DEMONSTRATION ===")
    
    # Create performance tester
    tester = PerformanceTester()
    
    # Test synchronous function
    def sync_function():
        import time
        time.sleep(0.001)  # Simulate work
        return "sync result"
    
    sync_result = await tester.benchmark("sync_function", sync_function, iterations=10)
    print(f"Synchronous function: {sync_result.avg_time:.6f}s average")
    
    # Test asynchronous function
    async def async_function():
        await asyncio.sleep(0.001)  # Simulate work
        return "async result"
    
    async_result = await tester.benchmark("async_function", async_function, iterations=10)
    print(f"Asynchronous function: {async_result.avg_time:.6f}s average")
    
    # Create benchmark suite
    suite = BenchmarkSuite("example_suite")
    suite.add_benchmark("test1", sync_function, iterations=5)
    suite.add_benchmark("test2", async_function, iterations=5)
    
    results = await suite.run_all()
    print(f"Benchmark suite completed: {len(results)} tests")
    
    # Stress test
    stress_result = await stress_test(
        async_function,
        concurrent_tasks=5,
        duration=1.0
    )
    print(f"Stress test: {stress_result['requests_per_second']:.2f} requests/sec")


# Load testing examples
async def demonstrate_load_testing():
    """Demonstration of load testing."""
    print("\n=== LOAD TESTING DEMONSTRATION ===")
    
    # Create load test configuration
    config = create_simple_load_test(
        url="http://localhost:8000/users",
        users=5,
        duration=2.0
    )
    
    print(f"Load test configuration: {config.concurrent_users} users, {config.duration}s")
    
    # Start application for testing
    import uvicorn
    import threading
    
    def run_app():
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
    
    # Start application in separate thread
    app_thread = threading.Thread(target=run_app, daemon=True)
    app_thread.start()
    
    # Wait for application to start
    await asyncio.sleep(2)
    
    try:
        # Execute load test
        async with LoadTester() as tester:
            result = await tester.run_load_test(config)
            
            print(f"Load test results:")
            print(f"  Total requests: {result.total_requests}")
            print(f"  Successful: {result.successful_requests}")
            print(f"  Failed: {result.failed_requests}")
            print(f"  Requests/sec: {result.requests_per_second:.2f}")
            print(f"  Average response time: {result.avg_response_time:.3f}s")
            print(f"  Error rate: {result.error_rate:.2%}")
            
            if result.status_codes:
                print("  Status codes:")
                for code, count in result.status_codes.items():
                    print(f"    {code}: {count}")
    
    except Exception as e:
        print(f"Error during load testing: {e}")


# Decorator examples
@with_fixtures("user", "post")
async def test_with_fixtures_example(user, post):
    """Example of using with_fixtures decorator."""
    print(f"\n=== TEST WITH FIXTURES ===")
    print(f"User from fixture: {user}")
    print(f"Post from fixture: {post}")
    return True


@with_database("test_db")
async def test_with_database_example(db, db_utils):
    """Example of using with_database decorator."""
    print(f"\n=== TEST WITH DATABASE ===")
    
    await db.setup()
    
    # Create table
    db.execute_script("CREATE TABLE test (id INTEGER, name TEXT)")
    
    # Insert data
    db.insert("test", {"id": 1, "name": "Test Data"})
    
    # Get data
    result = db.fetch_one("SELECT * FROM test WHERE id = ?", (1,))
    print(f"Data from database: {result}")
    
    await db.teardown()
    return True


@benchmark(name="example_benchmark", iterations=5)
async def test_benchmark_example():
    """Example of using benchmark decorator."""
    await asyncio.sleep(0.001)
    return "benchmark result"


# Main function
async def main():
    """Main function for demonstration."""
    print("DEMONSTRATION OF ENHANCED TESTING SYSTEM IN QakeAPI")
    print("=" * 60)
    
    # Demonstrate fixtures
    demonstrate_fixtures()
    
    # Demonstrate database
    await demonstrate_database()
    
    # Demonstrate mocks
    await demonstrate_mocks()
    
    # Demonstrate performance
    await demonstrate_performance()
    
    # Demonstrate decorators
    await test_with_fixtures_example()
    await test_with_database_example()
    await test_benchmark_example()
    
    # Demonstrate load testing
    await demonstrate_load_testing()
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETED")


if __name__ == "__main__":
    import uvicorn
    print("Starting Enhanced Testing Example API...")
    print("Available endpoints:")
    print("  GET /users - List users")
    print("  GET /users/{id} - Get user by ID")
    print("  POST /users - Create user")
    print("  GET /posts - List posts")
    
    uvicorn.run("enhanced_testing_example:app", host="0.0.0.0", port=8026, reload=False) 