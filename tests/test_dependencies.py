"""
Tests for dependency injection system.
"""

import pytest
from qakeapi.core.dependencies import Dependency, Depends, resolve_dependencies, resolve_dependency_values
from qakeapi.core.request import Request


class TestDependency:
    """Tests for Dependency class."""
    
    @pytest.mark.asyncio
    async def test_dependency_creation(self):
        """Test creating a dependency."""
        def get_value():
            return "test_value"
        
        dep = Dependency(get_value)
        assert dep.func == get_value
        assert dep.cache is False
        assert dep._cached is False
    
    @pytest.mark.asyncio
    async def test_dependency_resolve(self):
        """Test resolving a dependency."""
        def get_value():
            return "resolved_value"
        
        dep = Dependency(get_value)
        result = await dep.resolve()
        assert result == "resolved_value"
    
    @pytest.mark.asyncio
    async def test_dependency_with_cache(self):
        """Test dependency caching."""
        call_count = [0]
        
        def get_value():
            call_count[0] += 1
            return f"value_{call_count[0]}"
        
        dep = Dependency(get_value, cache=True)
        
        # First call
        result1 = await dep.resolve()
        assert result1 == "value_1"
        assert call_count[0] == 1
        
        # Second call should use cache
        result2 = await dep.resolve()
        assert result2 == "value_1"
        assert call_count[0] == 1  # Not called again
    
    @pytest.mark.asyncio
    async def test_dependency_with_kwargs(self):
        """Test dependency with keyword arguments."""
        def get_value(x: int, y: str = "default"):
            return f"{x}_{y}"
        
        dep = Dependency(get_value)
        result = await dep.resolve(x=10, y="test")
        assert result == "10_test"
    
    @pytest.mark.asyncio
    async def test_dependency_async_function(self):
        """Test dependency with async function."""
        async def get_async_value():
            return "async_value"
        
        dep = Dependency(get_async_value)
        result = await dep.resolve()
        assert result == "async_value"


class TestDepends:
    """Tests for Depends decorator."""
    
    def test_depends_creation(self):
        """Test creating a dependency with Depends."""
        def get_db():
            return "database"
        
        dep = Depends(get_db)
        assert isinstance(dep, Dependency)
        assert dep.func == get_db
    
    def test_depends_with_cache(self):
        """Test Depends with caching."""
        def get_config():
            return "config"
        
        dep = Depends(get_config, cache=True)
        assert isinstance(dep, Dependency)
        assert dep.cache is True
    
    def test_depends_with_existing_dependency(self):
        """Test Depends with existing Dependency object."""
        def get_value():
            return "value"
        
        existing_dep = Dependency(get_value)
        dep = Depends(existing_dep)
        assert dep is existing_dep


class TestResolveDependencies:
    """Tests for resolve_dependencies function."""
    
    def test_resolve_dependencies_with_depends(self):
        """Test resolving dependencies with Depends."""
        class MockRequest:
            pass
        
        request = MockRequest()
        
        def get_db():
            return "database"
        
        def handler(db=Depends(get_db), request=request):
            pass
        
        deps = resolve_dependencies(
            handler,
            path_params={},
            query_params={},
            request=request
        )
        
        assert "db" in deps
        assert isinstance(deps["db"], Dependency)
        assert "request" in deps
        assert deps["request"] == request
    
    def test_resolve_dependencies_with_path_params(self):
        """Test resolving dependencies with path parameters."""
        class MockRequest:
            pass
        
        request = MockRequest()
        
        def handler(id: int, name: str):
            pass
        
        deps = resolve_dependencies(
            handler,
            path_params={"id": "1", "name": "test"},
            query_params={},
            request=request
        )
        
        # Path params should be skipped
        assert "id" not in deps
        assert "name" not in deps
    
    def test_resolve_dependencies_with_body(self):
        """Test resolving dependencies with body data."""
        class MockRequest:
            pass
        
        request = MockRequest()
        body_data = {"key": "value"}
        
        def handler(body):
            pass
        
        deps = resolve_dependencies(
            handler,
            path_params={},
            query_params={},
            request=request,
            body_data=body_data
        )
        
        assert "body" in deps
        assert deps["body"] == body_data


class TestResolveDependencyValues:
    """Tests for resolve_dependency_values function."""
    
    @pytest.mark.asyncio
    async def test_resolve_dependency_values(self):
        """Test resolving dependency values."""
        def get_value():
            return "resolved"
        
        dependencies = {
            "value": Dependency(get_value),
            "static": "static_value"
        }
        
        resolved = await resolve_dependency_values(dependencies)
        
        assert resolved["value"] == "resolved"
        assert resolved["static"] == "static_value"
    
    @pytest.mark.asyncio
    async def test_resolve_dependency_values_with_context(self):
        """Test resolving dependencies with context."""
        def get_value(x: int):
            return f"value_{x}"
        
        dependencies = {
            "value": Dependency(get_value)
        }
        
        resolved = await resolve_dependency_values(dependencies, x=10)
        assert resolved["value"] == "value_10"

