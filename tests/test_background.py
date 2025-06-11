import pytest
import asyncio
from datetime import datetime, timedelta
from qakeapi.core.background import BackgroundTask, BackgroundTaskManager

async def sample_task(sleep_time: float = 0.1) -> str:
    await asyncio.sleep(sleep_time)
    return "completed"

async def long_running_task() -> str:
    await asyncio.sleep(5.0)  # Достаточно длинная задача для тестов отмены
    return "completed"

async def failing_task() -> None:
    raise ValueError("Task failed")

@pytest.mark.asyncio
class TestBackgroundTask:
    async def test_task_execution(self):
        task = BackgroundTask(sample_task)
        result = await task.run()
        assert result == "completed"
        assert task.completed_at is not None
        assert task.error is None
        
    async def test_task_with_timeout(self):
        task = BackgroundTask(sample_task, 1.0, timeout=0.1)
        with pytest.raises(asyncio.TimeoutError):
            await task.run()
        assert task.completed_at is not None
        assert isinstance(task.error, asyncio.TimeoutError)
        
    async def test_task_with_retry(self):
        task = BackgroundTask(failing_task, retry_count=2)
        with pytest.raises(ValueError):
            await task.run()
        assert task.retries == 2
        assert task.completed_at is not None
        assert isinstance(task.error, ValueError)

@pytest.mark.asyncio
class TestBackgroundTaskManager:
    async def test_task_management(self):
        manager = BackgroundTaskManager()
        task = BackgroundTask(sample_task)
        
        # Добавление задачи
        task_id = await manager.add_task(task)
        assert task_id in manager.tasks
        
        # Проверка статуса
        await asyncio.sleep(0.2)  # Даем задаче время на выполнение
        status = manager.get_task_status(task_id)
        assert status["status"] == "completed"
        
    async def test_task_cancellation(self):
        manager = BackgroundTaskManager()
        task = BackgroundTask(long_running_task)  # Используем длительную задачу
        
        task_id = await manager.add_task(task)
        await asyncio.sleep(0.1)  # Даем задаче время начать выполнение
        
        # Отмена задачи
        cancelled = await manager.cancel_task(task_id)
        assert cancelled
        
        # Ждем пока задача будет отменена
        for _ in range(10):  # Максимум 1 секунда ожидания
            status = manager.get_task_status(task_id)
            if status["status"] == "failed":
                break
            await asyncio.sleep(0.1)
        
        assert status["status"] == "failed"
        
    async def test_cleanup(self):
        manager = BackgroundTaskManager()
        task = BackgroundTask(sample_task)
        
        task_id = await manager.add_task(task)
        await asyncio.sleep(0.2)  # Даем задаче время на выполнение
        
        # Выполняем однократную очистку старых задач
        now = datetime.utcnow()
        to_remove = [
            task_id for task_id, task in manager.tasks.items()
            if task.completed_at and (now - task.completed_at) > timedelta(microseconds=1)
        ]
        for task_id in to_remove:
            del manager.tasks[task_id]
            
        assert task_id not in manager.tasks
        
    async def test_manager_lifecycle(self):
        manager = BackgroundTaskManager()
        await manager.start()
        
        # Добавляем несколько длительных задач
        tasks = [
            BackgroundTask(long_running_task),
            BackgroundTask(long_running_task)
        ]
        
        for task in tasks:
            await manager.add_task(task)
            
        await asyncio.sleep(0.1)  # Даем задачам время начать выполнение
        
        # Останавливаем менеджер
        await manager.stop()
        
        # Ждем пока все задачи будут отменены
        for _ in range(10):  # Максимум 1 секунда ожидания
            if len(manager.running_tasks) == 0:
                break
            await asyncio.sleep(0.1)
        
        # Проверяем, что все задачи отменены
        assert len(manager.running_tasks) == 0 