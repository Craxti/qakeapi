# -*- coding: utf-8 -*-
"""
WebSocket пример использования QakeAPI.
"""
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from qakeapi.core.application import Application
from qakeapi.core.websockets import WebSocket
from qakeapi.core.responses import Response, JSONResponse
from qakeapi.core.requests import Request

WEBSOCKET_PORT = 8006  # Используем фиксированный порт
MAX_ROOMS = 100  # Maximum number of rooms
MAX_CONNECTIONS_PER_ROOM = 50  # Maximum connections per room

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='websocket.log'
)
logger = logging.getLogger(__name__)

# Create application
app = Application()

@dataclass
class ChatRoom:
    """Room data structure for better management."""
    id: str
    connections: List[WebSocket]
    created_at: datetime
    last_activity: datetime

# Store active rooms
rooms: Dict[str, ChatRoom] = {}

def validate_room_id(room_id: str) -> bool:
    """Validate room ID format and constraints."""
    return (
        room_id.isalnum() and  # Only alphanumeric characters
        3 <= len(room_id) <= 50 and  # Length constraints
        len(rooms) < MAX_ROOMS  # Maximum rooms limit
    )

def validate_message(data: dict) -> bool:
    """Validate message format."""
    required_fields = {"type", "content", "sender"}
    return (
        all(field in data for field in required_fields) and
        isinstance(data["type"], str) and
        isinstance(data["content"], str) and
        isinstance(data["sender"], str) and
        len(data["content"]) <= 1000  # Message length limit
    )

@app.websocket("/ws/echo")
async def echo(websocket: WebSocket):
    """Simple echo server with improved error handling."""
    try:
        await websocket.accept()
        logger.info("New echo connection established")
        
        while True:
            try:
                message = await websocket.receive_text()
                if len(message) > 1000:  # Message size limit
                    await websocket.send_text("Error: Message too long")
                    continue
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                await websocket.send_text("Error: Internal server error")
                break
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        try:
            await websocket.close()
        except:
            pass

@app.websocket("/ws/chat/{room_id}")
async def chat(websocket: WebSocket, room_id: str):
    """Enhanced chat with room management and validation."""
    if not validate_room_id(room_id):
        await websocket.close(code=4000, reason="Invalid room ID")
        return

    try:
        # Create or update room
        if room_id not in rooms:
            if len(rooms) >= MAX_ROOMS:
                await websocket.close(code=4001, reason="Maximum rooms limit reached")
                return
            rooms[room_id] = ChatRoom(
                id=room_id,
                connections=[],
                created_at=datetime.now(),
                last_activity=datetime.now()
            )
        
        room = rooms[room_id]
        
        if len(room.connections) >= MAX_CONNECTIONS_PER_ROOM:
            await websocket.close(code=4002, reason="Room is full")
            return
        
        room.connections.append(websocket)
        room.last_activity = datetime.now()
        
        await websocket.accept()
        logger.info(f"New chat connection in room {room_id}")
        
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "content": f"Welcome to room {room_id}!",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                data = await websocket.receive_json()
                
                if not validate_message(data):
                    await websocket.send_json({
                        "type": "error",
                        "content": "Invalid message format",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                message = {
                    "type": data["type"],
                    "content": data["content"],
                    "sender": data["sender"],
                    "timestamp": datetime.now().isoformat()
                }
                
                room.last_activity = datetime.now()
                
                # Broadcast message to all connections in room
                for conn in room.connections:
                    if conn != websocket or message["type"] == "broadcast":
                        try:
                            await conn.send_json(message)
                        except Exception as e:
                            logger.error(f"Failed to send to connection: {str(e)}")
                            
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in room {room_id}")
        await websocket.send_json({
            "type": "error",
            "content": "Invalid JSON format",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Chat error in room {room_id}: {str(e)}")
    finally:
        # Cleanup connection and room
        if room_id in rooms:
            room = rooms[room_id]
            if websocket in room.connections:
                room.connections.remove(websocket)
            if not room.connections:
                del rooms[room_id]
        await websocket.close()
        logger.info(f"Chat connection closed in room {room_id}")

@app.get("/")
async def root(request: Request) -> Response:
    """Enhanced root endpoint with room statistics."""
    stats = {
        "status": "WebSocket server is running",
        "active_rooms": len(rooms),
        "total_connections": sum(len(room.connections) for room in rooms.values()),
        "server_time": datetime.now().isoformat()
    }
    return JSONResponse(stats)

if __name__ == "__main__":
    import uvicorn
    import asyncio
    
    async def start_server():
        config = uvicorn.Config(app, host="127.0.0.1", port=8006, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    
    asyncio.run(start_server())
