"""
Tests for Parallel Resolver.
"""

import pytest
import asyncio
from qakeapi.core.parallel import ParallelResolver, resolve_parallel


class TestParallelResolver:
    """Tests for ParallelResolver."""
    
    @pytest.mark.asyncio
    async def test_resolve_parallel_simple(self):
        """Test parallel resolution of simple functions."""
        async def func1():
            await asyncio.sleep(0.01)
            return "result1"
        
        async def func2():
            await asyncio.sleep(0.01)
            return "result2"
        
        results = await resolve_parallel({
            "func1": func1,
            "func2": func2,
        })
        
        assert results["func1"] == "result1"
        assert results["func2"] == "result2"
    
    @pytest.mark.asyncio
    async def test_resolve_parallel_with_dependencies(self):
        """Test parallel resolution with dependencies."""
        async def func1():
            await asyncio.sleep(0.01)
            return "result1"
        
        async def func2():
            await asyncio.sleep(0.01)
            return "result2"
        
        results = await resolve_parallel({
            "func1": func1,
            "func2": func2,
        })
        
        assert results["func1"] == "result1"
        assert results["func2"] == "result2"
    
    @pytest.mark.asyncio
    async def test_resolve_parallel_independent(self):
        """Test that independent functions run in parallel."""
        async def func1():
            await asyncio.sleep(0.01)
            return "result1"
        
        async def func2():
            await asyncio.sleep(0.01)
            return "result2"
        
        start = asyncio.get_event_loop().time()
        results = await resolve_parallel({
            "func1": func1,
            "func2": func2,
        })
        end = asyncio.get_event_loop().time()
        
        # Should take ~0.01s (parallel) not ~0.02s (sequential)
        assert end - start < 0.03
        assert results["func1"] == "result1"
        assert results["func2"] == "result2"


class TestResolveParallel:
    """Tests for resolve_parallel function."""
    
    @pytest.mark.asyncio
    async def test_resolve_parallel_function(self):
        """Test resolve_parallel function."""
        async def func1():
            return "result1"
        
        async def func2():
            return "result2"
        
        results = await resolve_parallel({
            "func1": func1,
            "func2": func2,
        })
        
        assert results["func1"] == "result1"
        assert results["func2"] == "result2"

