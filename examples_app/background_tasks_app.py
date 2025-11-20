# -*- coding: utf-8 -*-
"""
Background tasks example with QakeAPI.
"""
import sys
import os
import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import Field

# Initialize application
app = Application(
    title="Background Tasks Example",
    version="1.0.3",
    description="Background tasks functionality example with QakeAPI"
)

# Task status enum
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# Pydantic models
class TaskRequest(RequestModel):
    """Task request model"""
    task_type: str = Field(..., description="Type of task to execute")
    parameters: Optional[Dict] = Field({}, description="Task parameters")

# Background tasks storage
tasks = {}
task_counter = 0

async def process_task(task_id: str, task_type: str, parameters: Dict):
    """Process background task"""
    try:
        # Update task status to running
        tasks[task_id]["status"] = TaskStatus.RUNNING
        tasks[task_id]["started_at"] = datetime.utcnow()
        
        # Simulate different types of tasks
        if task_type == "email":
            await process_email_task(task_id, parameters)
        elif task_type == "report":
            await process_report_task(task_id, parameters)
        elif task_type == "data_processing":
            await process_data_task(task_id, parameters)
        else:
            await process_generic_task(task_id, parameters)
        
        # Mark task as completed
        tasks[task_id]["status"] = TaskStatus.COMPLETED
        tasks[task_id]["completed_at"] = datetime.utcnow()
        tasks[task_id]["result"] = {"message": f"Task {task_type} completed successfully"}
        
    except Exception as e:
        # Mark task as failed
        tasks[task_id]["status"] = TaskStatus.FAILED
        tasks[task_id]["completed_at"] = datetime.utcnow()
        tasks[task_id]["error"] = str(e)

async def process_email_task(task_id: str, parameters: Dict):
    """Process email sending task"""
    recipient = parameters.get("recipient", "user@example.com")
    subject = parameters.get("subject", "Test email")
    
    # Simulate email processing
    await asyncio.sleep(2)
    
    # Simulate email sending
    await asyncio.sleep(1)
    
    tasks[task_id]["progress"] = 100
    tasks[task_id]["result"] = {
        "message": "Email sent successfully",
        "recipient": recipient,
        "subject": subject
    }

async def process_report_task(task_id: str, parameters: Dict):
    """Process report generation task"""
    report_type = parameters.get("type", "summary")
    
    # Simulate report generation
    for i in range(10):
        await asyncio.sleep(0.5)
        tasks[task_id]["progress"] = (i + 1) * 10
    
    tasks[task_id]["result"] = {
        "message": "Report generated successfully",
        "report_type": report_type,
        "file_path": f"/reports/{report_type}_{task_id}.pdf"
    }

async def process_data_task(task_id: str, parameters: Dict):
    """Process data processing task"""
    data_size = parameters.get("size", 1000)
    
    # Simulate data processing
    for i in range(20):
        await asyncio.sleep(0.3)
        tasks[task_id]["progress"] = (i + 1) * 5
    
    tasks[task_id]["result"] = {
        "message": "Data processing completed",
        "processed_records": data_size,
        "output_file": f"/data/processed_{task_id}.csv"
    }

async def process_generic_task(task_id: str, parameters: Dict):
    """Process generic task"""
    duration = parameters.get("duration", 5)
    
    # Simulate generic task processing
    for i in range(duration):
        await asyncio.sleep(1)
        tasks[task_id]["progress"] = (i + 1) * (100 // duration)
    
    tasks[task_id]["result"] = {
        "message": "Generic task completed",
        "duration": duration
    }

@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "Background Tasks API is running",
        "total_tasks": len(tasks),
        "endpoints": {
            "/tasks": "GET - List all tasks",
            "/tasks/{task_id}": "GET - Get task status",
            "/tasks": "POST - Create new task",
            "/stats": "GET - Task statistics"
        }
    }

@app.post("/tasks")
@validate_request_body(TaskRequest)
async def create_task(request: Request):
    """Create new background task"""
    global task_counter
    task_counter += 1
    
    task_data = request.validated_data
    task_id = str(uuid.uuid4())
    
    # Create task record
    tasks[task_id] = {
        "id": task_id,
        "type": task_data.task_type,
        "parameters": task_data.parameters,
        "status": TaskStatus.PENDING,
        "progress": 0,
        "created_at": datetime.utcnow(),
        "started_at": None,
        "completed_at": None,
        "result": None,
        "error": None
    }
    
    # Start background task
    asyncio.create_task(
        process_task(task_id, task_data.task_type, task_data.parameters)
    )
    
    return {
        "message": "Task created successfully",
        "task_id": task_id,
        "type": task_data.task_type,
        "status": TaskStatus.PENDING
    }

@app.get("/tasks")
async def list_tasks(request: Request):
    """List all tasks"""
    task_list = []
    for task_id, task in tasks.items():
        task_list.append({
            "id": task_id,
            "type": task["type"],
            "status": task["status"],
            "progress": task.get("progress", 0),
            "created_at": task["created_at"].isoformat(),
            "started_at": task.get("started_at", "").isoformat() if task.get("started_at") else None,
            "completed_at": task.get("completed_at", "").isoformat() if task.get("completed_at") else None
        })
    
    return {
        "tasks": task_list,
        "total": len(tasks)
    }

@app.get("/tasks/{task_id}")
async def get_task(request: Request):
    task_id = request.path_params.get("task_id")
    """Get task status and details"""
    if task_id not in tasks:
        return Response.json(
            {"error": "Task not found"},
            status_code=404
        )
    
    task = tasks[task_id]
    
    return {
        "id": task["id"],
        "type": task["type"],
        "status": task["status"],
        "progress": task.get("progress", 0),
        "parameters": task["parameters"],
        "created_at": task["created_at"].isoformat(),
        "started_at": task.get("started_at", "").isoformat() if task.get("started_at") else None,
        "completed_at": task.get("completed_at", "").isoformat() if task.get("completed_at") else None,
        "result": task.get("result"),
        "error": task.get("error")
    }

@app.get("/stats")
async def get_task_stats(request: Request):
    """Get task statistics"""
    stats = {
        "total": len(tasks),
        "pending": 0,
        "running": 0,
        "completed": 0,
        "failed": 0
    }
    
    for task in tasks.values():
        stats[task["status"]] += 1
    
    # Calculate success rate
    success_rate = 0
    if stats["completed"] + stats["failed"] > 0:
        success_rate = stats["completed"] / (stats["completed"] + stats["failed"])
    
    return {
        "message": "Task statistics",
        "stats": stats,
        "success_rate": f"{success_rate:.2%}",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "background_tasks": "active",
        "total_tasks": len(tasks)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003) 