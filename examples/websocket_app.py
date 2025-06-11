import asyncio
import json
from typing import Dict, Set
import uvicorn
from qakeapi.core.application import Application
from qakeapi.core.websockets import WebSocket, WebSocketState
from qakeapi.core.dependencies import Dependency
from pydantic import BaseModel

# Создаем модели для документации
class MessageRequest(BaseModel):
    message: str
    type: str = "message"

class MessageResponse(BaseModel):
    message: str
    type: str
    sender: str = None

# Создаем приложение
app = Application(
    title="WebSocket Example",
    version="1.0.0",
    description="An example of WebSocket usage in QakeAPI"
)

# Создаем зависимость для хранения подключений
class ConnectionStore(Dependency):
    def __init__(self):
        super().__init__(scope="singleton")
        self.connected_clients: Set[WebSocket] = set()
        self.chat_rooms: Dict[str, Set[WebSocket]] = {}
        
    async def resolve(self):
        return self

connection_store = ConnectionStore()

@app.on_startup
async def register_dependencies():
    app.dependency_container.register(connection_store)

@app.websocket("/ws/chat/{room_id}")
async def chat_websocket(websocket: WebSocket):
    """WebSocket endpoint for chat functionality"""
    store = await connection_store.resolve()
    try:
        # Accept the connection
        await websocket.accept()
        
        # Get room ID from path parameters
        room_id = websocket.scope["path_params"]["room_id"]
        
        # Create room if it doesn't exist
        if room_id not in store.chat_rooms:
            store.chat_rooms[room_id] = set()
            
        # Add client to room
        store.chat_rooms[room_id].add(websocket)
        store.connected_clients.add(websocket)
        
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "message": f"Welcome to chat room {room_id}!"
        })
        
        # Broadcast join message
        await broadcast_to_room(room_id, {
            "type": "system",
            "message": "A new user has joined the chat"
        }, exclude=websocket)
        
        try:
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    # Add sender information
                    data["sender"] = str(id(websocket))
                    # Broadcast message to room
                    await broadcast_to_room(room_id, data)
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
                    
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
            
    finally:
        store = await connection_store.resolve()
        # Remove client from room and connected clients
        if room_id in store.chat_rooms:
            store.chat_rooms[room_id].discard(websocket)
            if not store.chat_rooms[room_id]:
                del store.chat_rooms[room_id]
        store.connected_clients.discard(websocket)
        
        if websocket.state == WebSocketState.CONNECTED:
            await websocket.close()
            
        # Broadcast leave message
        if room_id in store.chat_rooms:
            await broadcast_to_room(room_id, {
                "type": "system",
                "message": "A user has left the chat"
            })

async def broadcast_to_room(
    room_id: str,
    message: Dict,
    exclude: WebSocket = None
) -> None:
    """Broadcast message to all clients in a room"""
    store = await connection_store.resolve()
    if room_id in store.chat_rooms:
        for client in store.chat_rooms[room_id]:
            if client != exclude and client.state == WebSocketState.CONNECTED:
                try:
                    await client.send_json(message)
                except Exception:
                    pass

@app.websocket("/ws/echo")
async def echo_websocket(websocket: WebSocket):
    """Simple echo WebSocket endpoint"""
    try:
        await websocket.accept()
        
        async for message in websocket:
            await websocket.send_text(f"Echo: {message}")
    except Exception as e:
        if websocket.state == WebSocketState.CONNECTED:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
    finally:
        if websocket.state == WebSocketState.CONNECTED:
            await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 