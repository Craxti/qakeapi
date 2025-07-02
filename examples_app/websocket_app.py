# -*- coding: utf-8 -*-
"""
WebSocket example with QakeAPI.
"""
import sys
import os
import asyncio
import json
from datetime import datetime

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application, Request, Response
from qakeapi.validation.models import validate_request_body, RequestModel
from pydantic import Field

# Initialize application
app = Application(
    title="WebSocket Example",
    version="1.0.3",
    description="WebSocket functionality example with QakeAPI"
)

# Pydantic models
class BroadcastMessage(RequestModel):
    """Broadcast message model"""
    message: str = Field(..., description="Message to broadcast")

# WebSocket connections storage
websocket_connections = []
message_history = []

@app.get("/")
async def root(request: Request):
    """Root endpoint"""
    return {
        "message": "WebSocket API is running",
        "connections": len(websocket_connections),
        "messages_sent": len(message_history)
    }

@app.get("/stats")
async def get_stats(request: Request):
    """Get WebSocket statistics"""
    return {
        "active_connections": len(websocket_connections),
        "total_messages": len(message_history),
        "last_message": message_history[-1] if message_history else None
    }

@app.post("/broadcast")
@validate_request_body(BroadcastMessage)
async def broadcast_message(request: Request):
    """Broadcast message to all connected clients"""
    message_data = request.validated_data
    
    message = {
        "type": "broadcast",
        "message": message_data.message,
        "timestamp": datetime.utcnow().isoformat(),
        "sender": "server"
    }
    
    message_history.append(message)
    
    # Send to all connected WebSocket clients
    for connection in websocket_connections:
        try:
            await connection.send(json.dumps(message))
        except Exception as e:
            print(f"Error sending to connection: {e}")
            websocket_connections.remove(connection)
    
    return {"message": "Broadcast sent", "recipients": len(websocket_connections)}

@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time communication"""
    websocket_connections.append(websocket)
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "welcome",
            "message": "Connected to WebSocket server",
            "timestamp": datetime.utcnow().isoformat(),
            "connections": len(websocket_connections)
        }
        await websocket.send(json.dumps(welcome_message))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Echo message back
                response = {
                    "type": "echo",
                    "original_message": data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send(json.dumps(response))
                
                # Store in history
                message_history.append({
                    "type": "client_message",
                    "message": data,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002) 