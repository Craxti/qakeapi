import asyncio
import json
import logging
from typing import Dict, Set

import uvicorn
from pydantic import BaseModel

from qakeapi.core.application import Application
from qakeapi.core.dependencies import Dependency
from qakeapi.core.websockets import WebSocket, WebSocketState
from common.websocket_utils import handle_websocket_message, safe_close_websocket, send_error

# Настраиваем логирование
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
    description="An example of WebSocket usage in QakeAPI",
)

# Добавляем middleware для аутентификации WebSocket
@app.router.middleware()
async def websocket_auth_middleware(handler):
    async def wrapper(request):
        if request.type == "websocket":
            # Проверяем наличие токена в заголовках
            token = request.headers.get("authorization")
            if not token:
                return Response.json({"detail": "Unauthorized"}, status_code=403)
        return await handler(request)
    return wrapper


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
    room_id = None
    try:
        # Accept the connection
        await websocket.accept()
        logger.debug("WebSocket connection accepted")

        # Get room ID from path parameters
        room_id = websocket.scope["path_params"]["room_id"]
        logger.debug(f"Client joined room: {room_id}")

        # Create room if it doesn't exist
        if room_id not in store.chat_rooms:
            store.chat_rooms[room_id] = set()
            logger.debug(f"Created new room: {room_id}")

        # Add client to room
        store.chat_rooms[room_id].add(websocket)
        store.connected_clients.add(websocket)
        logger.debug(
            f"Added client to room {room_id}. Total clients in room: {len(store.chat_rooms[room_id])}"
        )

        # Send welcome message
        welcome_msg = {"type": "system", "message": f"Welcome to chat room {room_id}!"}
        await websocket.send_json(welcome_msg)
        logger.debug(f"Sent welcome message: {welcome_msg}")

        # Broadcast join message
        join_msg = {"type": "system", "message": "A new user has joined the chat"}
        await broadcast_to_room(room_id, join_msg, exclude=websocket)
        logger.debug("Broadcasted join message")

        async def handle_chat_message(data: Dict):
            data["sender"] = str(id(websocket))
            await broadcast_to_room(room_id, data)
            logger.debug(f"Broadcasted message to room {room_id}")

        # Handle messages
        async for message in websocket:
            await handle_websocket_message(websocket, message, handle_chat_message)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await safe_close_websocket(websocket, 1011)
    finally:
        if room_id:
            store = await connection_store.resolve()
            # Remove client from room and connected clients
            if room_id in store.chat_rooms:
                store.chat_rooms[room_id].discard(websocket)
                if not store.chat_rooms[room_id]:
                    del store.chat_rooms[room_id]
                logger.debug(f"Removed client from room {room_id}")
            store.connected_clients.discard(websocket)
            logger.debug("Removed client from connected clients")

            await safe_close_websocket(websocket)

            # Broadcast leave message
            if room_id in store.chat_rooms:
                leave_msg = {"type": "system", "message": "A user has left the chat"}
                await broadcast_to_room(room_id, leave_msg)
                logger.debug("Broadcasted leave message")


async def broadcast_to_room(
    room_id: str, message: Dict, exclude: WebSocket = None
) -> None:
    """Broadcast message to all clients in a room"""
    store = await connection_store.resolve()
    if room_id in store.chat_rooms:
        for client in store.chat_rooms[room_id]:
            if client != exclude and client.state == WebSocketState.CONNECTED:
                try:
                    await client.send_json(message)
                    logger.debug(f"Sent message to client in room {room_id}")
                except Exception as e:
                    logger.error(f"Error sending message to client: {e}")


@app.websocket("/ws/echo")
async def echo_websocket(websocket: WebSocket):
    """Simple echo WebSocket endpoint"""
    try:
        await websocket.accept()
        logger.debug("Echo WebSocket connection accepted")

        async def handle_echo_message(message: str):
            await websocket.send_text(f"Echo: {message}")
            logger.debug("Echo sent response")

        async for message in websocket:
            logger.debug(f"Echo received message: {message}")
            await handle_echo_message(message)
    except Exception as e:
        logger.error(f"Echo WebSocket error: {e}")
        await send_error(websocket, str(e))
    finally:
        await safe_close_websocket(websocket)


if __name__ == "__main__":
    from config import PORTS
    uvicorn.run(app, host="0.0.0.0", port=PORTS['websocket_app'], log_level="debug")
