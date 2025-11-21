"""
Enhanced tests for API Versioning System.

Tests the complete versioning system including:
- Multiple versioning strategies
- Deprecation warnings and sunset dates
- Version compatibility
- Middleware integration
"""

from datetime import date, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from qakeapi.api.versioning import (
    APIVersionManager,
    DeprecationWarning,
    HeaderVersionStrategy,
    PathVersionStrategy,
    QueryVersionStrategy,
    VersionCompatibilityChecker,
    VersionInfo,
    VersionManagerFactory,
    VersionStatus,
    VersionStrategy,
    deprecated_version,
    version_required,
)
from qakeapi.api.versioning_middleware import (
    VersionAnalyticsMiddleware,
    VersionCompatibilityMiddleware,
    VersioningMiddleware,
    VersioningMiddlewareFactory,
    VersionRouteMiddleware,
)


class TestVersionInfo:
    """Test VersionInfo dataclass."""

    def test_version_info_creation(self):
        """Test creating VersionInfo."""
        info = VersionInfo(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=date(2023, 1, 1),
            description="Initial version",
        )

        assert info.version == "v1"
        assert info.status == VersionStatus.ACTIVE
        assert info.release_date == date(2023, 1, 1)
        assert info.description == "Initial version"
        assert info.breaking_changes == []
        assert info.new_features == []
        assert info.bug_fixes == []

    def test_version_info_with_changes(self):
        """Test VersionInfo with breaking changes and features."""
        info = VersionInfo(
            version="v2",
            status=VersionStatus.ACTIVE,
            breaking_changes=["Removed deprecated endpoint"],
            new_features=["Added pagination"],
            bug_fixes=["Fixed authentication bug"],
        )

        assert info.breaking_changes == ["Removed deprecated endpoint"]
        assert info.new_features == ["Added pagination"]
        assert info.bug_fixes == ["Fixed authentication bug"]


class TestVersionStrategies:
    """Test versioning strategies."""

    def test_path_version_strategy(self):
        """Test PathVersionStrategy."""
        strategy = PathVersionStrategy(["v1", "v2"], "v1")

        # Test valid path
        request = Mock(path="/v1/users")
        version = strategy.extract_version(request)
        assert version == "v1"

        # Test invalid path
        request = Mock(path="/v3/users")
        version = strategy.extract_version(request)
        assert version is None

        # Test no version in path
        request = Mock(path="/users")
        version = strategy.extract_version(request)
        assert version is None

    def test_header_version_strategy(self):
        """Test HeaderVersionStrategy."""
        strategy = HeaderVersionStrategy(["v1", "v2"], "v1")

        # Test valid header
        request = Mock(headers={"accept-version": "v1"})
        version = strategy.extract_version(request)
        assert version == "v1"

        # Test multiple versions in header
        request = Mock(headers={"accept-version": "v1, v2;q=0.9"})
        version = strategy.extract_version(request)
        assert version == "v1"

        # Test invalid version
        request = Mock(headers={"accept-version": "v3"})
        version = strategy.extract_version(request)
        assert version is None

    def test_query_version_strategy(self):
        """Test QueryVersionStrategy."""
        strategy = QueryVersionStrategy(["v1", "v2"], "v1")

        # Test valid query parameter
        request = Mock(query_params={"version": "v1"})
        version = strategy.extract_version(request)
        assert version == "v1"

        # Test invalid version
        request = Mock(query_params={"version": "v3"})
        version = strategy.extract_version(request)
        assert version is None


class TestAPIVersionManager:
    """Test APIVersionManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = APIVersionManager(VersionStrategy.PATH)

        # Add strategies
        path_strategy = PathVersionStrategy(["v1", "v2"], "v1")
        header_strategy = HeaderVersionStrategy(["v1", "v2"], "v1")
        query_strategy = QueryVersionStrategy(["v1", "v2"], "v1")

        self.manager.add_strategy(VersionStrategy.PATH, path_strategy)
        self.manager.add_strategy(VersionStrategy.HEADER, header_strategy)
        self.manager.add_strategy(VersionStrategy.QUERY, query_strategy)

        # Register versions
        v1_info = VersionInfo(
            version="v1", status=VersionStatus.ACTIVE, release_date=date(2023, 1, 1)
        )
        v2_info = VersionInfo(
            version="v2", status=VersionStatus.ACTIVE, release_date=date(2023, 6, 1)
        )

        self.manager.register_version(v1_info)
        self.manager.register_version(v2_info)

    def test_register_version(self):
        """Test registering versions."""
        assert "v1" in self.manager.versions
        assert "v2" in self.manager.versions
        assert self.manager.versions["v1"].status == VersionStatus.ACTIVE

    def test_register_deprecated_version(self):
        """Test registering deprecated version."""
        v3_info = VersionInfo(
            version="v3",
            status=VersionStatus.DEPRECATED,
            deprecation_date=date(2024, 1, 1),
            sunset_date=date(2024, 12, 31),
        )

        self.manager.register_version(v3_info)

        assert "v3" in self.manager.versions
        assert self.manager.is_version_deprecated("v3")
        assert "v3" in self.manager.deprecation_warnings

    def test_extract_version_path(self):
        """Test extracting version from path."""
        request = Mock(path="/v1/users")
        version = self.manager.extract_version(request, VersionStrategy.PATH)
        assert version == "v1"

    def test_extract_version_header(self):
        """Test extracting version from header."""
        request = Mock(headers={"accept-version": "v2"})
        version = self.manager.extract_version(request, VersionStrategy.HEADER)
        assert version == "v2"

    def test_extract_version_query(self):
        """Test extracting version from query."""
        request = Mock(query_params={"version": "v2"})
        version = self.manager.extract_version(request, VersionStrategy.QUERY)
        assert version == "v2"

    def test_version_compatibility(self):
        """Test version compatibility."""
        self.manager.add_compatibility("v1", ["v2"])
        self.manager.add_compatibility("v2", ["v1"])

        assert self.manager.is_compatible("v1", "v2")
        assert self.manager.is_compatible("v2", "v1")
        assert self.manager.is_compatible("v1", "v1")
        assert not self.manager.is_compatible("v1", "v3")

    def test_get_active_versions(self):
        """Test getting active versions."""
        active_versions = self.manager.get_active_versions()
        assert "v1" in active_versions
        assert "v2" in active_versions

    def test_get_deprecated_versions(self):
        """Test getting deprecated versions."""
        v3_info = VersionInfo(version="v3", status=VersionStatus.DEPRECATED)
        self.manager.register_version(v3_info)

        deprecated_versions = self.manager.get_deprecated_versions()
        assert "v3" in deprecated_versions

    def test_sunset_version(self):
        """Test sunset version detection."""
        yesterday = date.today() - timedelta(days=1)
        v3_info = VersionInfo(
            version="v3", status=VersionStatus.DEPRECATED, sunset_date=yesterday
        )
        self.manager.register_version(v3_info)

        assert self.manager.is_version_sunset("v3")
        assert not self.manager.is_version_sunset("v1")


class TestVersionManagerFactory:
    """Test VersionManagerFactory."""

    def test_create_path_based_manager(self):
        """Test creating path-based manager."""
        manager = VersionManagerFactory.create_path_based_manager(["v1", "v2"], "v1")

        assert VersionStrategy.PATH in manager.strategies
        assert isinstance(manager.strategies[VersionStrategy.PATH], PathVersionStrategy)

    def test_create_header_based_manager(self):
        """Test creating header-based manager."""
        manager = VersionManagerFactory.create_header_based_manager(["v1", "v2"], "v1")

        assert VersionStrategy.HEADER in manager.strategies
        assert isinstance(
            manager.strategies[VersionStrategy.HEADER], HeaderVersionStrategy
        )

    def test_create_multi_strategy_manager(self):
        """Test creating multi-strategy manager."""
        manager = VersionManagerFactory.create_multi_strategy_manager(
            ["v1", "v2"], "v1"
        )

        assert VersionStrategy.PATH in manager.strategies
        assert VersionStrategy.HEADER in manager.strategies
        assert VersionStrategy.QUERY in manager.strategies


class TestVersionDecorators:
    """Test version decorators."""

    @pytest.mark.asyncio
    async def test_version_required_decorator(self):
        """Test version_required decorator."""

        @version_required("v2")
        async def test_handler():
            return "success"

        result = await test_handler()
        assert result == "success"
        assert hasattr(test_handler, "required_version")
        assert test_handler.required_version == "v2"

    @pytest.mark.asyncio
    async def test_deprecated_version_decorator(self):
        """Test deprecated_version decorator."""
        sunset_date = date(2024, 12, 31)

        @deprecated_version("v1", sunset_date)
        async def test_handler():
            return "success"

        result = await test_handler()
        assert result == "success"
        assert hasattr(test_handler, "deprecated_version")
        assert test_handler.deprecated_version == "v1"
        assert test_handler.sunset_date == sunset_date


class TestVersionCompatibilityChecker:
    """Test VersionCompatibilityChecker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = APIVersionManager()
        self.manager.add_compatibility("v1", ["v2"])
        self.manager.add_compatibility("v2", ["v1"])

        self.checker = VersionCompatibilityChecker(self.manager)

    def test_check_compatibility(self):
        """Test compatibility checking."""
        assert self.checker.check_compatibility("v1", "v2")
        assert self.checker.check_compatibility("v2", "v1")
        assert not self.checker.check_compatibility("v1", "v3")

    def test_get_migration_path(self):
        """Test migration path generation."""
        path = self.checker.get_migration_path("v1", "v2")
        assert path == ["v1", "v2"]


class TestVersioningMiddleware:
    """Test versioning middleware."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = VersionManagerFactory.create_multi_strategy_manager(
            ["v1", "v2"], "v1"
        )

        # Register versions
        v1_info = VersionInfo(version="v1", status=VersionStatus.ACTIVE)
        v2_info = VersionInfo(version="v2", status=VersionStatus.ACTIVE)
        self.manager.register_version(v1_info)
        self.manager.register_version(v2_info)

        self.middleware = VersioningMiddleware(self.manager)

    @pytest.mark.asyncio
    async def test_extract_path_version(self):
        """Test extracting version from path."""
        request = Mock(path="/v1/users")
        version = self.middleware._extract_path_version(request)
        assert version == "v1"

    @pytest.mark.asyncio
    async def test_extract_header_version(self):
        """Test extracting version from header."""
        request = Mock(headers={"accept-version": "v2"})
        version = self.middleware._extract_header_version(request)
        assert version == "v2"

    @pytest.mark.asyncio
    async def test_extract_query_version(self):
        """Test extracting version from query."""
        request = Mock(query_string=b"version=v2")
        version = self.middleware._extract_query_version(request)
        assert version == "v2"

    @pytest.mark.asyncio
    async def test_middleware_processing(self):
        """Test middleware processing."""
        request = Mock(path="/v1/users", headers={}, query_string=b"")

        async def handler(req):
            return Mock(headers={})

        response = await self.middleware(request, handler)

        assert hasattr(request, "api_version")
        assert request.api_version == "v1"

    @pytest.mark.asyncio
    async def test_deprecation_warning(self):
        """Test deprecation warning handling."""
        # Register deprecated version
        v3_info = VersionInfo(
            version="v3", status=VersionStatus.DEPRECATED, deprecation_date=date.today()
        )
        self.manager.register_version(v3_info)

        request = Mock(path="/v3/users", headers={}, query_string=b"")

        async def handler(req):
            return Mock(headers={})

        response = await self.middleware(request, handler)

        assert hasattr(request, "deprecation_warning")
        assert request.deprecation_warning.version == "v3"

    @pytest.mark.asyncio
    async def test_sunset_version_response(self):
        """Test sunset version response."""
        # Register sunset version
        yesterday = date.today() - timedelta(days=1)
        v3_info = VersionInfo(
            version="v3", status=VersionStatus.DEPRECATED, sunset_date=yesterday
        )
        self.manager.register_version(v3_info)

        request = Mock(path="/v3/users", headers={}, query_string=b"")

        async def handler(req):
            return Mock(headers={})

        response = await self.middleware(request, handler)

        # Should return 410 Gone response
        assert response.status_code == 410


class TestVersionRouteMiddleware:
    """Test version route middleware."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = APIVersionManager()
        self.middleware = VersionRouteMiddleware(self.manager)

    @pytest.mark.asyncio
    async def test_register_version_route(self):
        """Test registering version route."""

        async def handler(request):
            return "v1 handler"

        self.middleware.register_version_route("v1", "/users", handler)

        assert "v1" in self.middleware.version_routes
        assert "/users" in self.middleware.version_routes["v1"]

    @pytest.mark.asyncio
    async def test_version_specific_routing(self):
        """Test version-specific routing."""

        async def v1_handler(request):
            return "v1 handler"

        async def v2_handler(request):
            return "v2 handler"

        self.middleware.register_version_route("v1", "/users", v1_handler)
        self.middleware.register_version_route("v2", "/users", v2_handler)

        # Test v1 route
        request = Mock(path="/v1/users", api_version="v1")

        async def default_handler(req):
            return "default handler"

        response = await self.middleware(request, default_handler)
        assert response == "v1 handler"

        # Test v2 route
        request = Mock(path="/v2/users", api_version="v2")
        response = await self.middleware(request, default_handler)
        assert response == "v2 handler"


class TestVersionCompatibilityMiddleware:
    """Test version compatibility middleware."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = APIVersionManager()

        # Register versions
        v1_info = VersionInfo(version="v1", status=VersionStatus.ACTIVE)
        v2_info = VersionInfo(version="v2", status=VersionStatus.ACTIVE)
        self.manager.register_version(v1_info)
        self.manager.register_version(v2_info)

        # Add compatibility
        self.manager.add_compatibility("v1", ["v2"])
        self.manager.add_compatibility("v2", ["v1"])

        self.middleware = VersionCompatibilityMiddleware(self.manager)

    @pytest.mark.asyncio
    async def test_compatible_versions(self):
        """Test compatible versions."""
        request = Mock(api_version="v1")

        async def handler(req):
            return "success"

        response = await self.middleware(request, handler)
        assert response == "success"

    @pytest.mark.asyncio
    async def test_incompatible_versions(self):
        """Test incompatible versions."""
        request = Mock(api_version="v3")

        async def handler(req):
            return "success"

        response = await self.middleware(request, handler)
        assert response.status_code == 400


class TestVersionAnalyticsMiddleware:
    """Test version analytics middleware."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = APIVersionManager()
        self.middleware = VersionAnalyticsMiddleware(self.manager)

    @pytest.mark.asyncio
    async def test_usage_tracking(self):
        """Test usage tracking."""
        request = Mock(api_version="v1", path="/users")

        async def handler(req):
            return Mock(headers={})

        response = await self.middleware(request, handler)

        stats = self.middleware.get_usage_stats()
        assert stats["v1"] == 1

    @pytest.mark.asyncio
    async def test_multiple_requests(self):
        """Test multiple requests tracking."""
        request1 = Mock(api_version="v1", path="/users")
        request2 = Mock(api_version="v2", path="/users")
        request3 = Mock(api_version="v1", path="/users")

        async def handler(req):
            return Mock(headers={})

        await self.middleware(request1, handler)
        await self.middleware(request2, handler)
        await self.middleware(request3, handler)

        stats = self.middleware.get_usage_stats()
        assert stats["v1"] == 2
        assert stats["v2"] == 1

    def test_reset_stats(self):
        """Test resetting statistics."""
        self.middleware.usage_stats["v1"] = 5
        self.middleware.reset_stats()

        assert self.middleware.usage_stats == {}


class TestVersioningMiddlewareFactory:
    """Test VersioningMiddlewareFactory."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = APIVersionManager()

    def test_create_versioning_middleware(self):
        """Test creating versioning middleware."""
        middleware = VersioningMiddlewareFactory.create_versioning_middleware(
            self.manager
        )
        assert isinstance(middleware, VersioningMiddleware)

    def test_create_route_middleware(self):
        """Test creating route middleware."""
        middleware = VersioningMiddlewareFactory.create_route_middleware(self.manager)
        assert isinstance(middleware, VersionRouteMiddleware)

    def test_create_compatibility_middleware(self):
        """Test creating compatibility middleware."""
        middleware = VersioningMiddlewareFactory.create_compatibility_middleware(
            self.manager
        )
        assert isinstance(middleware, VersionCompatibilityMiddleware)

    def test_create_analytics_middleware(self):
        """Test creating analytics middleware."""
        middleware = VersioningMiddlewareFactory.create_analytics_middleware(
            self.manager
        )
        assert isinstance(middleware, VersionAnalyticsMiddleware)

    def test_create_full_stack(self):
        """Test creating full middleware stack."""
        stack = VersioningMiddlewareFactory.create_full_versioning_stack(self.manager)

        assert len(stack) == 4
        assert isinstance(stack[0], VersioningMiddleware)
        assert isinstance(stack[1], VersionRouteMiddleware)
        assert isinstance(stack[2], VersionCompatibilityMiddleware)
        assert isinstance(stack[3], VersionAnalyticsMiddleware)


class TestIntegration:
    """Integration tests for the complete versioning system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = VersionManagerFactory.create_multi_strategy_manager(
            ["v1", "v2"], "v1"
        )

        # Register versions with different statuses
        v1_info = VersionInfo(
            version="v1", status=VersionStatus.ACTIVE, release_date=date(2023, 1, 1)
        )
        v2_info = VersionInfo(
            version="v2",
            status=VersionStatus.DEPRECATED,
            deprecation_date=date(2024, 1, 1),
            sunset_date=date(2024, 12, 31),
        )

        self.manager.register_version(v1_info)
        self.manager.register_version(v2_info)

        # Add compatibility
        self.manager.add_compatibility("v1", ["v2"])
        self.manager.add_compatibility("v2", ["v1"])

    @pytest.mark.asyncio
    async def test_complete_versioning_flow(self):
        """Test complete versioning flow."""
        # Create middleware stack
        middleware_stack = VersioningMiddlewareFactory.create_full_versioning_stack(
            self.manager
        )

        # Test request processing
        request = Mock(path="/v1/users", headers={}, query_string=b"")

        async def handler(req):
            return Mock(headers={})

        # Process through middleware stack
        response = await middleware_stack[0](request, handler)

        # Check that version was extracted
        assert hasattr(request, "api_version")
        assert request.api_version == "v1"

        # Check that version is active
        assert not self.manager.is_version_deprecated("v1")
        assert not self.manager.is_version_sunset("v1")

    @pytest.mark.asyncio
    async def test_deprecated_version_flow(self):
        """Test deprecated version flow."""
        middleware = VersioningMiddleware(self.manager)

        request = Mock(path="/v2/users", headers={}, query_string=b"")

        async def handler(req):
            return Mock(headers={})

        response = await middleware(request, handler)

        # Check deprecation warning
        assert hasattr(request, "deprecation_warning")
        assert request.deprecation_warning.version == "v2"

    def test_version_info_serialization(self):
        """Test version info serialization."""
        v1_info = VersionInfo(
            version="v1",
            status=VersionStatus.ACTIVE,
            release_date=date(2023, 1, 1),
            breaking_changes=["Removed old endpoint"],
            new_features=["Added pagination"],
            bug_fixes=["Fixed auth bug"],
        )

        # Test that all fields are properly set
        assert v1_info.version == "v1"
        assert v1_info.status == VersionStatus.ACTIVE
        assert v1_info.release_date == date(2023, 1, 1)
        assert v1_info.breaking_changes == ["Removed old endpoint"]
        assert v1_info.new_features == ["Added pagination"]
        assert v1_info.bug_fixes == ["Fixed auth bug"]
