# Background Tasks

QakeAPI supports running tasks in the background, independent of the request/response cycle.

**Why QakeAPI background tasks:** `add_background_task()` — no Celery or Redis for fire-and-forget jobs. Response returns immediately; task runs after. Same pattern as FastAPI's `BackgroundTasks`, but built into core. Use for emails, reports, webhooks; for queues, add Redis later.

## Basic Usage

Run a task in the background:

```python
from qakeapi.core.background import add_background_task

@app.post("/process")
async def process_data(request):
    data = await request.json()
    
    # Run task in background
    await add_background_task(process_heavy_task, data)
    
    # Return immediately
    return {"message": "Processing started", "task_id": "123"}
```

## Task Functions

Define background task functions:

```python
async def send_email(email: str, subject: str, body: str):
    """Background task to send email."""
    # Simulate email sending
    await asyncio.sleep(1)
    print(f"Email sent to {email}")

@app.post("/users")
async def create_user(request):
    data = await request.json()
    
    # Send welcome email in background
    await add_background_task(
        send_email,
        email=data["email"],
        subject="Welcome",
        body="Thanks for joining!"
    )
    
    return {"message": "User created"}
```

## Sync Tasks

Background tasks can be synchronous:

```python
def generate_report(data):
    """Synchronous background task."""
    # Heavy computation
    report = process_data(data)
    save_to_file(report)
    return report

@app.post("/reports")
async def create_report(request):
    data = await request.json()
    
    # Sync task runs in thread pool
    await add_background_task(generate_report, data)
    
    return {"message": "Report generation started"}
```

## Task with Multiple Arguments

Pass multiple arguments:

```python
async def process_order(order_id: int, user_id: int, items: list):
    """Process order with multiple arguments."""
    for item in items:
        await process_item(order_id, item)
    await notify_user(user_id, order_id)

@app.post("/orders")
async def create_order(request):
    data = await request.json()
    
    await add_background_task(
        process_order,
        order_id=data["id"],
        user_id=data["user_id"],
        items=data["items"]
    )
    
    return {"message": "Order processing started"}
```

## Task Results

Get task results (if needed):

```python
from qakeapi.core.background import BackgroundTaskManager

task_manager = BackgroundTaskManager()

async def calculate_result(data):
    # Long calculation
    await asyncio.sleep(5)
    return {"result": sum(data)}

@app.post("/calculate")
async def start_calculation(request):
    data = await request.json()
    
    # Add task and wait for result
    task_id = await task_manager.add_task(
        calculate_result,
        data,
        wait=True  # Wait for completion
    )
    
    task = task_manager.tasks[task_id]
    return {"result": task.result}
```

## Error Handling

Handle errors in background tasks:

```python
async def risky_task(data):
    try:
        # Risky operation
        await process_data(data)
    except Exception as e:
        # Log error
        logger.error(f"Task failed: {e}")
        # Optionally emit error event
        await app.emit("task:failed", {"error": str(e)})

@app.post("/process")
async def process(request):
    data = await request.json()
    
    # Task errors don't affect response
    await add_background_task(risky_task, data)
    
    return {"message": "Processing started"}
```

## Use Cases

### 1. Email Sending

```python
async def send_notification_email(user_id: int, message: str):
    user = await get_user(user_id)
    await email_service.send(user.email, message)

@app.post("/notify")
async def notify_user(request):
    data = await request.json()
    await add_background_task(send_notification_email, data["user_id"], data["message"])
    return {"message": "Notification queued"}
```

### 2. File Processing

```python
def process_uploaded_file(file_path: str):
    # Process file (CPU-intensive)
    result = analyze_file(file_path)
    save_results(result)

@app.post("/upload")
async def upload_file(request):
    file_path = await save_uploaded_file(request)
    await add_background_task(process_uploaded_file, file_path)
    return {"message": "File uploaded, processing started"}
```

### 3. Data Synchronization

```python
async def sync_with_external_api(data):
    await external_api.sync(data)
    await update_cache(data)

@app.post("/sync")
async def trigger_sync(request):
    data = await request.json()
    await add_background_task(sync_with_external_api, data)
    return {"message": "Sync started"}
```

## Best Practices

1. **Use for long operations** - don't block the request/response cycle
2. **Handle errors** - background tasks can fail silently
3. **Use async for I/O** - async tasks are more efficient
4. **Use sync for CPU-bound** - sync tasks run in thread pool
5. **Don't depend on results** - background tasks are fire-and-forget by default


