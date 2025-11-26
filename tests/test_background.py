"""
Tests for Background Tasks system.
"""

import pytest
import asyncio
from qakeapi.core.background import (
    BackgroundTask,
    BackgroundTaskManager,
    add_background_task,
)


class TestBackgroundTask:
    """Tests for BackgroundTask."""
    
    def test_background_task_creation(self):
        """Test background task creation."""
        def task_func(x: int) -> int:
            return x * 2
        
        task = BackgroundTask(task_func, 5)
        
        assert task.func == task_func
        assert task.args == (5,)
        assert task.task_id is not None
        assert task.created_at is not None
        assert task.started_at is None
        assert task.completed_at is None
    
    @pytest.mark.asyncio
    async def test_background_task_run(self):
        """Test background task execution."""
        async def task_func(x: int) -> int:
            await asyncio.sleep(0.001)
            return x * 2
        
        task = BackgroundTask(task_func, 5)
        result = await task.run()
        
        assert result == 10
        assert task.started_at is not None
        assert task.completed_at is not None
        assert task.result == 10
        assert task.error is None
    
    @pytest.mark.asyncio
    async def test_background_task_with_error(self):
        """Test background task with error."""
        async def task_func():
            raise ValueError("Test error")
        
        task = BackgroundTask(task_func)
        
        with pytest.raises(ValueError, match="Test error"):
            await task.run()
        
        assert task.error is not None
        assert isinstance(task.error, ValueError)


class TestBackgroundTaskManager:
    """Tests for BackgroundTaskManager."""
    
    @pytest.mark.asyncio
    async def test_add_task(self):
        """Test adding background task."""
        manager = BackgroundTaskManager()
        
        async def task_func(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2
        
        task_id = await manager.add_task(task_func, 5)
        
        assert task_id is not None
        assert task_id in manager.tasks
        
        # Wait for task to complete
        await asyncio.sleep(0.1)
        
        task = manager.get_task(task_id)
        assert task is not None
        assert task.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_get_task(self):
        """Test getting task by ID."""
        manager = BackgroundTaskManager()
        
        async def task_func() -> str:
            return "completed"
        
        task_id = await manager.add_task(task_func)
        await asyncio.sleep(0.05)
        
        task = manager.get_task(task_id)
        assert task is not None
        assert task.task_id == task_id
    
    @pytest.mark.asyncio
    async def test_get_task_status(self):
        """Test getting task status."""
        manager = BackgroundTaskManager()
        
        async def task_func() -> str:
            await asyncio.sleep(0.01)
            return "completed"
        
        task_id = await manager.add_task(task_func)
        
        status = manager.get_task_status(task_id)
        assert status["task_id"] == task_id
        assert status["status"] in ["running", "completed"]
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self):
        """Test getting nonexistent task."""
        manager = BackgroundTaskManager()
        
        task = manager.get_task("nonexistent")
        assert task is None
        
        status = manager.get_task_status("nonexistent")
        assert status["status"] == "not_found"


class TestAddBackgroundTask:
    """Tests for add_background_task function."""
    
    @pytest.mark.asyncio
    async def test_add_background_task(self):
        """Test add_background_task function."""
        async def task_func(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2
        
        task_id = await add_background_task(task_func, 5)
        
        assert task_id is not None
        assert isinstance(task_id, str)


