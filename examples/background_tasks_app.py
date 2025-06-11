import asyncio
import uvicorn
from qakeapi.core.application import Application
from qakeapi.core.responses import Response
from qakeapi.core.requests import Request
from qakeapi.core.dependencies import Dependency
from pydantic import BaseModel

# Создаем модели для документации
class TaskRequest(BaseModel):
    sleep_time: float = 5.0

class TaskResponse(BaseModel):
    task_id: str
    message: str

class TaskStatus(BaseModel):
    status: str
    error: str = None

# Создаем приложение
app = Application(
    title="Background Tasks Example",
    version="1.0.0",
    description="An example of background tasks in QakeAPI"
)

# Создаем зависимость для хранения задач
class TaskStore(Dependency):
    def __init__(self):
        super().__init__(scope="singleton")
        self.tasks = {}
        
    async def resolve(self):
        return self.tasks

task_store = TaskStore()

@app.on_startup
async def register_dependencies():
    app.dependency_container.register(task_store)

async def long_running_task(sleep_time: float) -> None:
    """Пример длительной задачи"""
    await asyncio.sleep(sleep_time)
    print(f"Задача выполнена после {sleep_time} секунд")

@app.post("/tasks",
    summary="Create a new task",
    description="Creates a new background task that sleeps for the specified time",
    request_model=TaskRequest,
    response_model=TaskResponse
)
async def create_task(request: Request):
    """Создание новой фоновой задачи"""
    try:
        data = await request.json()
        sleep_time = float(data.get("sleep_time", 5.0))
        
        task_id = await app.add_background_task(
            long_running_task,
            sleep_time,
            task_id=f"task_{sleep_time}"
        )
        
        return Response.json({
            "task_id": task_id,
            "message": "Task created successfully"
        })
    except Exception as e:
        return Response.json(
            {"error": str(e)},
            status_code=400
        )

@app.get("/tasks/{task_id}",
    summary="Get task status",
    description="Returns the status of a background task",
    response_model=TaskStatus
)
async def get_task_status(request: Request):
    """Получение статуса задачи"""
    task_id = request.path_params["task_id"]
    status = app.get_task_status(task_id)
    return Response.json(status)

@app.delete("/tasks/{task_id}",
    summary="Cancel task",
    description="Cancels a running background task",
    response_model=TaskResponse
)
async def cancel_task(request: Request):
    """Отмена задачи"""
    task_id = request.path_params["task_id"]
    cancelled = await app.cancel_background_task(task_id)
    
    if cancelled:
        return Response.json({
            "task_id": task_id,
            "message": "Task cancelled successfully"
        })
    return Response.json(
        {"task_id": task_id, "message": "Task not found or already completed"},
        status_code=404
    )

# Пример задачи, которая может завершиться с ошибкой
async def failing_task() -> None:
    await asyncio.sleep(1)
    raise ValueError("Произошла ошибка в задаче")

@app.post("/failing-task",
    summary="Create a failing task",
    description="Creates a task that will fail after 1 second",
    response_model=TaskResponse
)
async def create_failing_task(request: Request):
    """Создание задачи, которая завершится с ошибкой"""
    task_id = await app.add_background_task(
        failing_task,
        retry_count=2  # Попробуем выполнить задачу 3 раза
    )
    
    return Response.json({
        "task_id": task_id,
        "message": "Failing task created"
    })

# Пример задачи с таймаутом
async def timeout_task() -> None:
    await asyncio.sleep(10)
    print("Эта строка не должна быть напечатана")

@app.post("/timeout-task",
    summary="Create a timeout task",
    description="Creates a task that will timeout after 2 seconds",
    response_model=TaskResponse
)
async def create_timeout_task(request: Request):
    """Создание задачи с таймаутом"""
    task_id = await app.add_background_task(
        timeout_task,
        timeout=2.0  # Задача будет отменена через 2 секунды
    )
    
    return Response.json({
        "task_id": task_id,
        "message": "Timeout task created"
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 