import asyncio
import uvicorn
from qakeapi.core.application import Application
from qakeapi.core.responses import JSONResponse

app = Application()

async def long_running_task(sleep_time: float) -> None:
    """Пример длительной задачи"""
    await asyncio.sleep(sleep_time)
    print(f"Задача выполнена после {sleep_time} секунд")

@app.route("/tasks", methods=["POST"])
async def create_task(request):
    """Создание новой фоновой задачи"""
    try:
        data = await request.json()
        sleep_time = float(data.get("sleep_time", 5.0))
        
        task_id = await app.add_background_task(
            long_running_task,
            sleep_time,
            task_id=f"task_{sleep_time}"
        )
        
        return JSONResponse({
            "task_id": task_id,
            "message": "Task created successfully"
        })
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=400
        )

@app.route("/tasks/{task_id}", methods=["GET"])
async def get_task_status(request):
    """Получение статуса задачи"""
    task_id = request.path_params["task_id"]
    status = app.get_task_status(task_id)
    return JSONResponse(status)

@app.route("/tasks/{task_id}", methods=["DELETE"])
async def cancel_task(request):
    """Отмена задачи"""
    task_id = request.path_params["task_id"]
    cancelled = await app.cancel_background_task(task_id)
    
    if cancelled:
        return JSONResponse({
            "message": "Task cancelled successfully"
        })
    return JSONResponse(
        {"message": "Task not found or already completed"},
        status_code=404
    )

# Пример задачи, которая может завершиться с ошибкой
async def failing_task() -> None:
    await asyncio.sleep(1)
    raise ValueError("Произошла ошибка в задаче")

@app.route("/failing-task", methods=["POST"])
async def create_failing_task(request):
    """Создание задачи, которая завершится с ошибкой"""
    task_id = await app.add_background_task(
        failing_task,
        retry_count=2  # Попробуем выполнить задачу 3 раза
    )
    
    return JSONResponse({
        "task_id": task_id,
        "message": "Failing task created"
    })

# Пример задачи с таймаутом
async def timeout_task() -> None:
    await asyncio.sleep(10)
    print("Эта строка не должна быть напечатана")

@app.route("/timeout-task", methods=["POST"])
async def create_timeout_task(request):
    """Создание задачи с таймаутом"""
    task_id = await app.add_background_task(
        timeout_task,
        timeout=2.0  # Задача будет отменена через 2 секунды
    )
    
    return JSONResponse({
        "task_id": task_id,
        "message": "Timeout task created"
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 