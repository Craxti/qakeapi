"""
Tests for Hybrid Executor (sync/async conversion).
"""

import pytest
import asyncio
from qakeapi.core.hybrid import hybrid_executor, run_hybrid, sync_to_async


class TestHybridExecutor:
    """Tests for hybrid executor."""
    
    def test_sync_function_execution(self):
        """Test that sync function works."""
        @hybrid_executor
        def sync_func(x: int, y: int) -> int:
            return x + y
        
        result = asyncio.run(sync_func(1, 2))
        assert result == 3
    
    @pytest.mark.asyncio
    async def test_async_function_execution(self):
        """Test that async function works."""
        @hybrid_executor
        async def async_func(x: int, y: int) -> int:
            await asyncio.sleep(0.001)
            return x + y
        
        result = await async_func(1, 2)
        assert result == 3
    
    @pytest.mark.asyncio
    async def test_run_hybrid_sync(self):
        """Test run_hybrid with sync function."""
        def sync_func(x: int) -> int:
            return x * 2
        
        result = await run_hybrid(sync_func, 5)
        assert result == 10
    
    @pytest.mark.asyncio
    async def test_run_hybrid_async(self):
        """Test run_hybrid with async function."""
        async def async_func(x: int) -> int:
            await asyncio.sleep(0.001)
            return x * 2
        
        result = await run_hybrid(async_func, 5)
        assert result == 10
    
    @pytest.mark.asyncio
    async def test_sync_to_async(self):
        """Test sync_to_async conversion."""
        def sync_func(x: int) -> int:
            return x + 1
        
        async_func = sync_to_async(sync_func)
        result = await async_func(5)
        assert result == 6
    
    def test_sync_function_with_exception(self):
        """Test sync function with exception."""
        @hybrid_executor
        def sync_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            asyncio.run(sync_func())
    
    @pytest.mark.asyncio
    async def test_async_function_with_exception(self):
        """Test async function with exception."""
        @hybrid_executor
        async def async_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            await async_func()
    
    @pytest.mark.asyncio
    async def test_run_hybrid_with_kwargs(self):
        """Test run_hybrid with keyword arguments."""
        def sync_func(x: int, y: int = 10) -> int:
            return x + y
        
        result = await run_hybrid(sync_func, 5, y=20)
        assert result == 25


