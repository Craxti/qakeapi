"""
Tests for enhanced testing framework.
"""
import pytest
import asyncio
import tempfile
import time
from unittest.mock import patch, AsyncMock
from pathlib import Path

from qakeapi.testing.fixtures import (
    FixtureFactory,
    TestFixtures,
    FixtureConfig,
    with_fixtures,
    user_fixture,
    post_fixture,
)
from qakeapi.testing.database import (
    TestDatabase,
    DatabaseTestUtils,
    with_database,
    test_database,
)
from qakeapi.testing.mocks import (
    MockService,
    MockExternalAPI,
    MockResponse,
    with_mock_service,
    create_user_service,
)
from qakeapi.testing.performance import (
    PerformanceTester,
    BenchmarkSuite,
    benchmark,
    stress_test,
)
from qakeapi.testing.load_testing import (
    LoadTester,
    LoadTestConfig,
    LoadTestResult,
    create_simple_load_test,
)


class TestFixtureFactory:
    """Test fixture factory."""

    def test_fixture_factory_init(self):
        """Test fixture factory initialization."""
        factory = FixtureFactory()
        assert factory.config.seed is None
        assert factory.config.locale == "en_US"

    def test_fixture_factory_with_seed(self):
        """Test fixture factory with seed."""
        config = FixtureConfig(seed=42)
        factory = FixtureFactory(config)
        assert factory.config.seed == 42

    def test_text_generation(self):
        """Test text generation."""
        factory = FixtureFactory()
        text = factory.text(10, 20)
        assert 10 <= len(text) <= 20
        assert text.isalnum()

    def test_email_generation(self):
        """Test email generation."""
        factory = FixtureFactory()
        email = factory.email()
        assert "@" in email
        assert email.endswith(".com")

    def test_name_generation(self):
        """Test name generation."""
        factory = FixtureFactory()
        name = factory.name()
        assert " " in name
        assert len(name.split()) == 2

    def test_uuid_generation(self):
        """Test UUID generation."""
        factory = FixtureFactory()
        uuid_val = factory.uuid()
        assert len(uuid_val) == 36
        assert uuid_val.count("-") == 4

    def test_integer_generation(self):
        """Test integer generation."""
        factory = FixtureFactory()
        num = factory.integer(1, 10)
        assert 1 <= num <= 10

    def test_float_generation(self):
        """Test float generation."""
        factory = FixtureFactory()
        num = factory.float(0.0, 1.0)
        assert 0.0 <= num <= 1.0

    def test_boolean_generation(self):
        """Test boolean generation."""
        factory = FixtureFactory()
        bool_val = factory.boolean()
        assert isinstance(bool_val, bool)

    def test_choice_generation(self):
        """Test choice generation."""
        factory = FixtureFactory()
        choices = ["a", "b", "c"]
        choice = factory.choice(choices)
        assert choice in choices

    def test_list_generation(self):
        """Test list generation."""
        factory = FixtureFactory()
        items = factory.list(lambda: factory.integer(1, 5), 2, 4)
        assert 2 <= len(items) <= 4
        assert all(1 <= item <= 5 for item in items)


class TestTestFixtures:
    """Test test fixtures."""

    def test_fixtures_init(self):
        """Test fixtures initialization."""
        fixtures = TestFixtures()
        assert fixtures._fixtures == {}
        assert fixtures._fixture_factories == {}

    def test_register_fixture(self):
        """Test fixture registration."""
        fixtures = TestFixtures()

        def test_factory():
            return {"test": "data"}

        fixtures.register_fixture("test", test_factory)
        assert "test" in fixtures._fixture_factories

    def test_get_fixture(self):
        """Test getting fixture."""
        fixtures = TestFixtures()

        def test_factory():
            return {"test": "data"}

        fixtures.register_fixture("test", test_factory)
        result = fixtures.get_fixture("test")
        assert result == {"test": "data"}

    def test_get_fixture_cached(self):
        """Test fixture caching."""
        fixtures = TestFixtures()

        call_count = 0

        def test_factory():
            nonlocal call_count
            call_count += 1
            return {"test": "data"}

        fixtures.register_fixture("test", test_factory)

        # First call should execute factory
        fixtures.get_fixture("test")
        assert call_count == 1

        # Second call should use cache
        fixtures.get_fixture("test")
        assert call_count == 1

    def test_create_fixture(self):
        """Test creating new fixture instance."""
        fixtures = TestFixtures()

        call_count = 0

        def test_factory():
            nonlocal call_count
            call_count += 1
            return {"test": "data"}

        fixtures.register_fixture("test", test_factory)

        # Create new instance
        fixtures.create_fixture("test")
        assert call_count == 1

        # Create another instance
        fixtures.create_fixture("test")
        assert call_count == 2

    def test_clear_fixtures(self):
        """Test clearing fixtures."""
        fixtures = TestFixtures()

        def test_factory():
            return {"test": "data"}

        fixtures.register_fixture("test", test_factory)
        fixtures.get_fixture("test")  # Cache it

        fixtures.clear_fixtures()
        assert fixtures._fixtures == {}


class TestDatabaseTestUtils:
    """Test database test utilities."""

    def test_database_utils_init(self):
        """Test database utils initialization."""
        utils = DatabaseTestUtils()
        assert utils.databases == {}

    def test_create_database(self):
        """Test database creation."""
        utils = DatabaseTestUtils()
        db = utils.create_database("test_db")
        assert "test_db" in utils.databases
        assert isinstance(db, TestDatabase)

    def test_get_database(self):
        """Test getting database."""
        utils = DatabaseTestUtils()
        db = utils.create_database("test_db")
        retrieved_db = utils.get_database("test_db")
        assert retrieved_db is db

    def test_get_database_not_found(self):
        """Test getting non-existent database."""
        utils = DatabaseTestUtils()
        with pytest.raises(ValueError):
            utils.get_database("non_existent")


class TestTestDatabase:
    """Test test database."""

    def test_database_init(self):
        """Test database initialization."""
        db = TestDatabase()
        assert db.db_path == ":memory:"
        assert db.connection is None

    def test_database_init_with_path(self):
        """Test database initialization with path."""
        db = TestDatabase("test.db")
        assert db.db_path == "test.db"

    @pytest.mark.asyncio
    async def test_database_setup_teardown(self):
        """Test database setup and teardown."""
        db = TestDatabase()

        # Setup
        await db.setup()
        assert db.connection is not None

        # Teardown
        await db.teardown()
        assert db.connection is None

    @pytest.mark.asyncio
    async def test_database_execute(self):
        """Test database execution."""
        db = TestDatabase()
        await db.setup()

        cursor = db.execute("SELECT 1")
        result = cursor.fetchone()
        assert result == (1,)

        await db.teardown()

    @pytest.mark.asyncio
    async def test_database_insert_fetch(self):
        """Test database insert and fetch."""
        db = TestDatabase()
        await db.setup()

        # Create table
        db.execute_script(
            """
            CREATE TABLE test (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """
        )

        # Insert data
        data = {"name": "test"}
        row_id = db.insert("test", data)
        assert row_id == 1

        # Fetch data
        result = db.fetch_one("SELECT * FROM test WHERE id = ?", (row_id,))
        assert result == (1, "test")

        await db.teardown()


class TestMockService:
    """Test mock service."""

    def test_mock_service_init(self):
        """Test mock service initialization."""
        service = MockService("test")
        assert service.name == "test"
        assert service._responses == {}
        assert service._call_history == []

    def test_add_response(self):
        """Test adding response."""
        service = MockService("test")
        response = MockResponse(status=200, body={"test": "data"})

        service.add_response("GET", "/test", response)
        assert "GET:/test" in service._responses

    def test_get_response(self):
        """Test getting response."""
        service = MockService("test")
        response = MockResponse(status=200, body={"test": "data"})

        service.add_response("GET", "/test", response)
        retrieved_response = service.get_response("GET", "/test")
        assert retrieved_response is response

    def test_get_default_response(self):
        """Test getting default response."""
        service = MockService("test")
        default_response = MockResponse(status=404, body="Not found")
        service.set_default_response(default_response)

        response = service.get_response("GET", "/unknown")
        assert response is default_response

    def test_record_call(self):
        """Test recording call."""
        service = MockService("test")
        headers = {"Content-Type": "application/json"}
        body = {"test": "data"}

        service.record_call("POST", "/test", headers, body)
        assert len(service._call_history) == 1

        call = service._call_history[0]
        assert call["method"] == "POST"
        assert call["path"] == "/test"
        assert call["headers"] == headers
        assert call["body"] == body

    def test_get_call_count(self):
        """Test getting call count."""
        service = MockService("test")

        service.record_call("GET", "/test", {}, {})
        service.record_call("POST", "/test", {}, {})
        service.record_call("GET", "/other", {}, {})

        assert service.get_call_count() == 3
        assert service.get_call_count("GET") == 2
        assert service.get_call_count("GET", "/test") == 1


class TestPerformanceTester:
    """Test performance tester."""

    @pytest.mark.asyncio
    async def test_performance_tester_init(self):
        """Test performance tester initialization."""
        tester = PerformanceTester()
        assert tester.results == []

    @pytest.mark.asyncio
    async def test_benchmark_sync_function(self):
        """Test benchmarking sync function."""
        tester = PerformanceTester()

        def test_func():
            time.sleep(0.001)  # Small delay

        result = await tester.benchmark("test", test_func, iterations=5)

        assert result.name == "test"
        assert result.iterations == 5
        assert result.total_time > 0
        assert result.avg_time > 0

    @pytest.mark.asyncio
    async def test_benchmark_async_function(self):
        """Test benchmarking async function."""
        tester = PerformanceTester()

        async def test_func():
            await asyncio.sleep(0.001)  # Small delay

        result = await tester.benchmark("test", test_func, iterations=5)

        assert result.name == "test"
        assert result.iterations == 5
        assert result.total_time > 0
        assert result.avg_time > 0

    @pytest.mark.asyncio
    async def test_get_result(self):
        """Test getting result."""
        tester = PerformanceTester()

        def test_func():
            pass

        result = await tester.benchmark("test", test_func, iterations=1)
        retrieved_result = tester.get_result("test")
        assert retrieved_result is result

    @pytest.mark.asyncio
    async def test_clear_results(self):
        """Test clearing results."""
        tester = PerformanceTester()

        def test_func():
            pass

        await tester.benchmark("test", test_func, iterations=1)
        assert len(tester.results) == 1

        tester.clear_results()
        assert len(tester.results) == 0


class TestBenchmarkSuite:
    """Test benchmark suite."""

    def test_benchmark_suite_init(self):
        """Test benchmark suite initialization."""
        suite = BenchmarkSuite("test_suite")
        assert suite.name == "test_suite"
        assert suite.benchmarks == []

    def test_add_benchmark(self):
        """Test adding benchmark."""
        suite = BenchmarkSuite("test_suite")

        def test_func():
            pass

        suite.add_benchmark("test", test_func, iterations=10)
        assert len(suite.benchmarks) == 1

        name, func, config = suite.benchmarks[0]
        assert name == "test"
        assert func == test_func
        assert config["iterations"] == 10

    @pytest.mark.asyncio
    async def test_run_all(self):
        """Test running all benchmarks."""
        suite = BenchmarkSuite("test_suite")

        def test_func():
            pass

        suite.add_benchmark("test1", test_func, iterations=1)
        suite.add_benchmark("test2", test_func, iterations=1)

        results = await suite.run_all()
        assert len(results) == 2
        assert results[0].name == "test1"
        assert results[1].name == "test2"


class TestLoadTester:
    """Test load tester."""

    @pytest.mark.asyncio
    async def test_load_tester_init(self):
        """Test load tester initialization."""
        async with LoadTester() as tester:
            assert tester.results == []

    @pytest.mark.asyncio
    async def test_load_test_config(self):
        """Test load test configuration."""
        config = LoadTestConfig(
            url="http://localhost:8000", method="GET", concurrent_users=5, duration=1.0
        )

        assert config.url == "http://localhost:8000"
        assert config.method == "GET"
        assert config.concurrent_users == 5
        assert config.duration == 1.0

    @pytest.mark.asyncio
    async def test_create_simple_load_test(self):
        """Test creating simple load test."""
        config = create_simple_load_test(
            "http://localhost:8000", users=5, duration=10.0
        )

        assert config.url == "http://localhost:8000"
        assert config.method == "GET"
        assert config.concurrent_users == 5
        assert config.duration == 10.0


# Integration tests
@pytest.mark.asyncio
async def test_with_fixtures_decorator():
    """Test with_fixtures decorator."""

    @with_fixtures("user", "post")
    async def test_function(user, post):
        assert "id" in user
        assert "title" in post
        return True

    result = await test_function()
    assert result is True


@pytest.mark.asyncio
async def test_with_database_decorator():
    """Test with_database decorator."""

    @with_database("test_db")
    async def test_function(db, db_utils):
        assert db is not None
        assert db_utils is not None
        await db.setup()

        # Test database operations
        db.execute_script("CREATE TABLE test (id INTEGER, name TEXT)")
        db.insert("test", {"id": 1, "name": "test"})

        result = db.fetch_one("SELECT * FROM test WHERE id = ?", (1,))
        assert result == (1, "test")

        await db.teardown()
        return True

    result = await test_function()
    assert result is True


@pytest.mark.asyncio
async def test_benchmark_decorator():
    """Test benchmark decorator."""

    @benchmark(name="test_benchmark", iterations=2)
    async def test_function():
        await asyncio.sleep(0.001)
        return "test"

    result = await test_function()
    assert result.name == "test_benchmark"
    assert result.iterations == 2


@pytest.mark.asyncio
async def test_stress_test():
    """Test stress test."""

    async def test_function():
        await asyncio.sleep(0.001)
        return "test"

    result = await stress_test(test_function, concurrent_tasks=2, duration=0.1)

    assert result["total_requests"] > 0
    assert result["concurrent_tasks"] == 2
    assert result["requests_per_second"] > 0
