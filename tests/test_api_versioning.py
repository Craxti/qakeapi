"""Tests for API versioning system."""

import pytest
import asyncio
from datetime import datetime, timedelta, date
from unittest.mock import Mock, MagicMock

from qakeapi.api.versioning import (
    APIVersionManager, 
    PathVersionStrategy, 
    HeaderVersionStrategy,
    CombinedVersionStrategy,
    VersionInfo,
    version_route
)
from qakeapi.api.deprecation import (
    DeprecationManager, 
    DeprecationWarning, 
    DeprecationLevel,
    deprecated,
    DeprecationInfo
)
from qakeapi.core.application import Application
from qakeapi.core.requests import Request
from qakeapi.api.versioning_middleware import APIVersioningMiddleware


class TestPathVersionStrategy:
    """Test path-based versioning strategy."""
    
    def test_extract_version_from_path(self):
        """Test version extraction from URL path."""
        strategy = PathVersionStrategy(["v1", "v2", "v3"])
        
        # Test valid versions
        request = Mock()
        request.path = "/v1/users"
        assert strategy.extract_version(request) == "v1"
        
        request.path = "/v2/api/data"
        assert strategy.extract_version(request) == "v2"
        
        request.path = "/v3/"
        assert strategy.extract_version(request) == "v3"
        
        # Test invalid versions
        request.path = "/users"
        assert strategy.extract_version(request) is None
        
        request.path = "/v4/users"
        assert strategy.extract_version(request) == "v4"  # Still extracts
    
    def test_version_support_check(self):
        """Test version support checking."""
        strategy = PathVersionStrategy(["v1", "v2", "v3"])
        
        assert strategy.is_version_supported("v1") is True
        assert strategy.is_version_supported("v2") is True
        assert strategy.is_version_supported("v3") is True
        assert strategy.is_version_supported("v4") is False
    
    def test_default_version(self):
        """Test default version."""
        strategy = PathVersionStrategy(["v1", "v2", "v3"], "v2")
        assert strategy.get_default_version() == "v2"


class TestHeaderVersionStrategy:
    """Test header-based versioning strategy."""
    
    def test_extract_version_from_header(self):
        """Test version extraction from Accept-Version header."""
        strategy = HeaderVersionStrategy(["v1", "v2", "v3"])
        
        # Test valid version header
        request = Mock()
        request.headers = {b'accept-version': b'v2'}
        assert strategy.extract_version(request) == "v2"
        
        # Test missing header
        request.headers = {}
        assert strategy.extract_version(request) == ""
        
        # Test empty header
        request.headers = {b'accept-version': b''}
        assert strategy.extract_version(request) == ""
    
    def test_version_support_check(self):
        """Test version support checking."""
        strategy = HeaderVersionStrategy(["v1", "v2", "v3"])
        
        assert strategy.is_version_supported("v1") is True
        assert strategy.is_version_supported("v2") is True
        assert strategy.is_version_supported("v3") is True
        assert strategy.is_version_supported("v4") is False


class TestCombinedVersionStrategy:
    """Test combined versioning strategy."""
    
    def test_extract_version_priority(self):
        """Test version extraction priority (path over header)."""
        path_strategy = PathVersionStrategy(["v1", "v2", "v3"])
        header_strategy = HeaderVersionStrategy(["v1", "v2", "v3"])
        strategy = CombinedVersionStrategy(path_strategy, header_strategy)
        
        # Path should take priority
        request = Mock()
        request.path = "/v2/users"
        request.headers = {b'accept-version': b'v3'}
        assert strategy.extract_version(request) == "v2"
        
        # Header when no path version
        request.path = "/users"
        request.headers = {b'accept-version': b'v3'}
        assert strategy.extract_version(request) == "v3"
        
        # None when neither present
        request.path = "/users"
        request.headers = {}
        assert strategy.extract_version(request) is None
    
    def test_combined_supported_versions(self):
        """Test combined supported versions."""
        path_strategy = PathVersionStrategy(["v1", "v2"])
        header_strategy = HeaderVersionStrategy(["v2", "v3"])
        strategy = CombinedVersionStrategy(path_strategy, header_strategy)
        
        expected = ["v1", "v2", "v3"]
        assert sorted(strategy.supported_versions) == sorted(expected)


class TestAPIVersionManager:
    """Test API version manager."""
    
    def setup_method(self):
        """Setup test method."""
        self.strategy = PathVersionStrategy(["v1", "v2"], "v1")
        self.manager = APIVersionManager(self.strategy)
    
    def test_register_version_handler(self):
        """Test registering version handlers."""
        handler = Mock()
        self.manager.register_version_handler("v1", "/users", handler)
        
        assert "v1" in self.manager.version_handlers
        assert "/users" in self.manager.version_handlers["v1"]
        assert self.manager.version_handlers["v1"]["/users"] == handler
    
    def test_get_version_handler(self):
        """Test getting version handler."""
        handler = Mock()
        self.manager.register_version_handler("v1", "/users", handler)
        
        retrieved_handler = self.manager.get_version_handler("v1", "/users")
        assert retrieved_handler == handler
        
        # Test non-existent handler
        assert self.manager.get_version_handler("v2", "/users") is None
    
    def test_get_supported_versions(self):
        """Test getting supported versions."""
        versions = self.manager.get_supported_versions()
        assert versions == ["v1", "v2"]
    
    def test_add_version_info(self):
        """Test adding version information."""
        info = VersionInfo(
            version="v1",
            release_date=datetime(2024, 1, 1),
            deprecated=False
        )
        self.manager.add_version_info("v1", info)
        
        retrieved_info = self.manager.get_version_info("v1")
        assert retrieved_info == info
    
    def test_get_version_from_request(self):
        """Test getting version from request."""
        request = Mock()
        request.path = "/v2/users"
        
        version = self.manager.get_version_from_request(request)
        assert version == "v2"
    
    def test_get_version_from_request_default(self):
        """Test getting default version when no version in request."""
        request = Mock()
        request.path = "/users"
        
        version = self.manager.get_version_from_request(request)
        assert version == "v1"
    
    def test_get_version_compatibility_matrix(self):
        """Test version compatibility matrix."""
        matrix = self.manager.get_version_compatibility_matrix()
        
        assert "v1" in matrix
        assert "v2" in matrix
        assert matrix["v1"]["v1"] is True
        assert matrix["v1"]["v2"] is False  # Different major versions
        assert matrix["v2"]["v2"] is True
    
    def test_generate_changelog(self):
        """Test changelog generation."""
        # Add version info
        info_v1 = VersionInfo(
            version="v1",
            release_date=datetime(2024, 1, 1),
            deprecated=False,
            new_features=["Feature 1"]
        )
        info_v2 = VersionInfo(
            version="v2",
            release_date=datetime(2024, 6, 1),
            deprecated=True,
            sunset_date=datetime(2025, 6, 1),
            breaking_changes=["Breaking change"]
        )
        
        self.manager.add_version_info("v1", info_v1)
        self.manager.add_version_info("v2", info_v2)
        
        changelog = self.manager.generate_changelog()
        
        assert "versions" in changelog
        assert "v1" in changelog["versions"]
        assert "v2" in changelog["versions"]
        assert changelog["latest_version"] == "v2"
        assert "v2" in changelog["deprecated_versions"]


class TestDeprecationManager:
    """Test deprecation manager."""
    
    def setup_method(self):
        """Setup test method."""
        self.manager = DeprecationManager()
    
    def test_add_deprecation(self):
        """Test adding deprecation warning."""
        deprecation = DeprecationWarning(
            feature="old_feature",
            version="v1",
            deprecation_date=datetime(2024, 6, 1),
            sunset_date=datetime(2025, 6, 1)
        )
        self.manager.add_deprecation(deprecation)
        
        assert "old_feature" in self.manager.deprecations
        assert self.manager.deprecations["old_feature"] == deprecation
    
    def test_is_deprecated(self):
        """Test checking if feature is deprecated."""
        deprecation = DeprecationWarning(
            feature="old_feature",
            version="v1",
            deprecation_date=datetime(2024, 6, 1),
            level=DeprecationLevel.DEPRECATED
        )
        self.manager.add_deprecation(deprecation)
        
        assert self.manager.is_deprecated("old_feature") is True
        assert self.manager.is_deprecated("new_feature") is False
    
    def test_is_sunset(self):
        """Test checking if feature is sunset."""
        # Past sunset date
        deprecation = DeprecationWarning(
            feature="sunset_feature",
            version="v1",
            deprecation_date=datetime(2024, 6, 1),
            sunset_date=datetime(2023, 6, 1)  # Past date
        )
        self.manager.add_deprecation(deprecation)
        
        assert self.manager.is_sunset("sunset_feature") is True
        
        # Future sunset date
        deprecation_future = DeprecationWarning(
            feature="future_feature",
            version="v1",
            deprecation_date=datetime(2024, 6, 1),
            sunset_date=datetime(2030, 6, 1)  # Far future date
        )
        self.manager.add_deprecation(deprecation_future)
        
        assert self.manager.is_sunset("future_feature") is False
    
    def test_check_deprecation_warning(self):
        """Test deprecation warning generation."""
        deprecation = DeprecationWarning(
            feature="old_feature",
            version="v1",
            deprecation_date=datetime(2023, 6, 1),  # Past date
            sunset_date=datetime(2030, 6, 1),  # Far future date
            replacement="new_feature"
        )
        self.manager.add_deprecation(deprecation)
        
        request = Mock()
        request.add_header = Mock()
        
        warning = self.manager.check_deprecation("old_feature", request)
        
        assert warning is not None
        assert "old_feature" in warning
        assert "new_feature" in warning
        request.add_header.assert_called_once()
    
    def test_check_deprecation_sunset_error(self):
        """Test deprecation error for sunset features."""
        deprecation = DeprecationWarning(
            feature="sunset_feature",
            version="v1",
            deprecation_date=datetime(2024, 6, 1),
            sunset_date=datetime(2023, 6, 1)  # Past date
        )
        self.manager.add_deprecation(deprecation)
        
        with pytest.raises(Exception):  # DeprecationError
            self.manager.check_deprecation("sunset_feature")
    
    def test_get_active_deprecations(self):
        """Test getting active deprecations."""
        # Active deprecation
        deprecation_active = DeprecationWarning(
            feature="active_feature",
            version="v1",
            deprecation_date=datetime(2023, 6, 1)  # Past date
        )
        
        # Future deprecation
        deprecation_future = DeprecationWarning(
            feature="future_feature",
            version="v1",
            deprecation_date=datetime(2030, 6, 1)  # Far future date
        )
        
        self.manager.add_deprecation(deprecation_active)
        self.manager.add_deprecation(deprecation_future)
        
        active = self.manager.get_active_deprecations()
        assert len(active) == 1
        assert active[0].feature == "active_feature"


class TestVersionRouteDecorator:
    """Test version route decorator."""
    
    def test_version_route_decorator(self):
        """Test version route decorator."""
        @version_route("v2", "/users")
        def get_users():
            return {"users": []}
        
        assert hasattr(get_users, 'version_info')
        assert get_users.version_info["version"] == "v2"
        assert get_users.version_info["path"] == "/users"


class TestDeprecatedDecorator:
    """Test deprecated decorator."""
    
    def test_deprecated_decorator(self):
        """Test deprecated decorator."""
        @deprecated(
            feature="old_feature",
            version="v1",
            deprecation_date=datetime(2024, 6, 1),
            replacement="new_feature"
        )
        def handler():
            return "old"
        
        assert hasattr(handler, 'deprecation_info')
        assert handler.deprecation_info["feature"] == "old_feature"
        assert handler.deprecation_info["replacement"] == "new_feature"


class TestApplicationIntegration:
    """Test API versioning integration with Application."""
    
    @pytest.mark.asyncio
    async def test_application_versioning_endpoints(self):
        """Test versioning endpoints in application."""
        app = Application(
            title="Test API",
            version="1.0.3",
            description="Test API"
        )
        
        # Test versions endpoint
        request = Mock()
        response = await app.api_versions(request)
        
        assert "current_version" in response
        assert "supported_versions" in response
        assert "default_version" in response
        assert "version_info" in response
    
    @pytest.mark.asyncio
    async def test_application_changelog_endpoint(self):
        """Test changelog endpoint in application."""
        app = Application(
            title="Test API",
            version="1.0.3",
            description="Test API"
        )
        
        request = Mock()
        response = await app.api_changelog(request)
        
        assert "versions" in response
        assert "latest_version" in response
        assert "deprecated_versions" in response
    
    @pytest.mark.asyncio
    async def test_application_deprecations_endpoint(self):
        """Test deprecations endpoint in application."""
        app = Application(
            title="Test API",
            version="1.0.3",
            description="Test API"
        )
        
        request = Mock()
        response = await app.api_deprecations(request)
        
        assert "active_deprecations" in response
        assert "sunset_features" in response


class TestAPIVersioningMiddleware:
    """Test API versioning middleware."""
    
    def test_middleware_initialization(self):
        """Test middleware initialization."""
        strategy = PathVersionStrategy(["v1", "v2"])
        manager = APIVersionManager(strategy)
        middleware = APIVersioningMiddleware(manager)
        
        assert middleware.version_manager == manager
    
    @pytest.mark.asyncio
    async def test_middleware_request_processing(self):
        """Test middleware request processing."""
        strategy = PathVersionStrategy(["v1", "v2"])
        manager = APIVersionManager(strategy)
        middleware = APIVersioningMiddleware(manager)
        
        # Mock request and response
        request = Mock()
        request.path = "/v2/users"
        request.headers = {}
        
        response = Mock()
        response.headers = []
        
        # Create async mock for call_next
        async def async_call_next(req):
            return response
        
        call_next = async_call_next
        
        # Process request
        result = await middleware(request, call_next)
        
        # Check that version was extracted and added to request
        assert hasattr(request, 'api_version')
        assert request.api_version == "v2"
        
        # Check response headers
        assert (b'X-API-Version', b'v2') in response.headers
        assert (b'X-API-Supported-Versions', b'v1,v2') in response.headers


class TestDeprecationManager:
    """Test deprecation manager."""
    
    def test_add_deprecation(self):
        """Test adding deprecation information."""
        manager = DeprecationManager()
        
        deprecation = DeprecationInfo(
            feature="old_endpoint",
            version="v1",
            deprecation_date=datetime(2024, 6, 1),
            sunset_date=datetime(2025, 6, 1),
            replacement="new_endpoint",
            migration_guide="https://docs.example.com/migration"
        )
        
        manager.add_deprecation("old_endpoint", deprecation)
        
        assert "old_endpoint" in manager.deprecations
        assert manager.deprecations["old_endpoint"] == deprecation
    
    def test_get_active_deprecations(self):
        """Test getting active deprecations."""
        manager = DeprecationManager()
        
        # Add deprecation
        deprecation = DeprecationInfo(
            feature="old_endpoint",
            version="v1",
            deprecation_date=datetime(2024, 6, 1),
            sunset_date=datetime(2025, 6, 1),
            replacement="new_endpoint",
            migration_guide="https://docs.example.com/migration"
        )
        
        manager.add_deprecation("old_endpoint", deprecation)
        
        active = manager.get_active_deprecations()
        assert len(active) == 1
        assert active[0]["feature"] == "old_endpoint"
    
    def test_get_sunset_features(self):
        """Test getting sunset features."""
        manager = DeprecationManager()
        
        # Add expired deprecation
        deprecation = DeprecationInfo(
            feature="old_endpoint",
            version="v1",
            deprecation_date=datetime(2023, 6, 1),
            sunset_date=datetime(2024, 1, 1),  # Past date
            replacement="new_endpoint",
            migration_guide="https://docs.example.com/migration"
        )
        
        manager.add_deprecation("old_endpoint", deprecation)
        
        sunset = manager.get_sunset_features()
        assert "old_endpoint" in sunset


class TestIntegration:
    """Integration tests for API versioning."""
    
    def test_full_versioning_workflow(self):
        """Test complete versioning workflow."""
        # Setup
        strategy = PathVersionStrategy(["v1", "v2", "v3"], "v1")
        manager = APIVersionManager(strategy)
        
        # Add version info
        info = VersionInfo(
            version="v1",
            release_date=datetime(2024, 1, 1),
            deprecated=False,
            new_features=["Basic API"]
        )
        manager.add_version_info("v1", info)
        
        # Register handlers
        handler1 = Mock()
        handler2 = Mock()
        manager.register_version_handler("v1", "/users", handler1)
        manager.register_version_handler("v2", "/users", handler2)
        
        # Test request processing
        request = Mock()
        request.path = "/v2/users"
        
        version = manager.get_version_from_request(request)
        handler = manager.get_version_handler(version, "/users")
        
        assert version == "v2"
        assert handler == handler2
        assert manager.is_version_deprecated("v1") is False
    
    def test_deprecation_workflow(self):
        """Test deprecation workflow."""
        # Setup managers
        strategy = PathVersionStrategy(["v1", "v2"])
        version_manager = APIVersionManager(strategy)
        deprecation_manager = DeprecationManager()
        
        # Add deprecation
        deprecation = DeprecationInfo(
            feature="v1_api",
            version="v1",
            deprecation_date=datetime(2024, 6, 1),
            sunset_date=datetime(2025, 6, 1),
            replacement="v2_api",
            migration_guide="https://docs.example.com/migration"
        )
        deprecation_manager.add_deprecation("v1_api", deprecation)
        
        # Mark version as deprecated
        info = VersionInfo(
            version="v1",
            release_date=datetime(2024, 1, 1),
            deprecated=True
        )
        version_manager.add_version_info("v1", info)
        
        # Test deprecation check
        assert version_manager.is_version_deprecated("v1") is True
        assert len(deprecation_manager.get_active_deprecations()) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 