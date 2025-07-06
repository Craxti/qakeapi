"""Enhanced WebSocket system with broadcast, pub/sub, and reconnect support."""

import json
import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, Optional, Union, Set, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class WebSocketState(Enum):
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    RECONNECTING = "RECONNECTING"

@dataclass
class WebSocketMessage:
    """WebSocket message with metadata."""
    type: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: Optional[str] = None
    room: Optional[str] = None

class WebSocketConnection:
    """Enhanced WebSocket connection with reconnect support."""
    
    def __init__(self, scope: Dict, receive: Any, send: Any, connection_id: str = None):
        self.scope = scope
        self.receive = receive
        self.send = send
        self.connection_id = connection_id or str(uuid.uuid4())
        self.state = WebSocketState.CONNECTING
        self.client = scope.get("client", None)
        self.path = scope.get("path", "")
        self.path_params = {}
        self.rooms: Set[str] = set()
        self.last_ping: Optional[datetime] = None
        self.last_pong: Optional[datetime] = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1.0
        self._ping_task: Optional[asyncio.Task] = None
        self._heartbeat_interval = 30.0
        logger.debug(f"Created WebSocket connection {self.connection_id}")

    async def accept(self, subprotocol: Optional[str] = None) -> None:
        """Accept the WebSocket connection."""
        if self.state != WebSocketState.CONNECTING:
            raise RuntimeError("WebSocket is not in CONNECTING state")

        await self.send({"type": "websocket.accept", "subprotocol": subprotocol})
        self.state = WebSocketState.CONNECTED
        self._start_heartbeat()
        logger.info(f"WebSocket {self.connection_id} connected")

    async def close(self, code: int = 1000, reason: Optional[str] = None) -> None:
        """Close the WebSocket connection."""
        if self.state == WebSocketState.DISCONNECTED:
            raise RuntimeError("WebSocket is already disconnected")

        self._stop_heartbeat()
        await self.send({"type": "websocket.close", "code": code, "reason": reason})
        self.state = WebSocketState.DISCONNECTED
        logger.info(f"WebSocket {self.connection_id} disconnected")

    async def send_text(self, data: str) -> None:
        """Send text data."""
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError("WebSocket is not connected")

        await self.send({"type": "websocket.send", "text": data})

    async def send_json(self, data: Any) -> None:
        """Send JSON data."""
        await self.send_text(json.dumps(data))

    async def send_bytes(self, data: bytes) -> None:
        """Send binary data."""
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError("WebSocket is not connected")

        await self.send({"type": "websocket.send", "bytes": data})

    async def send_ping(self, data: bytes = b"") -> None:
        """Send a ping frame."""
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError("WebSocket is not connected")

        self.last_ping = datetime.now()
        await self.send({"type": "websocket.send", "bytes": data, "ping": True})

    async def send_pong(self, data: bytes = b"") -> None:
        """Send a pong frame."""
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError("WebSocket is not connected")

        await self.send({"type": "websocket.send", "bytes": data, "pong": True})

    async def receive_text(self) -> str:
        """Receive text data."""
        message = await self.receive()
        if message["type"] == "websocket.disconnect":
            self.state = WebSocketState.DISCONNECTED
            raise RuntimeError("WebSocket disconnected")
        return message.get("text", "")

    async def receive_json(self) -> Any:
        """Receive JSON data."""
        data = await self.receive_text()
        return json.loads(data)

    async def receive_bytes(self) -> bytes:
        """Receive binary data."""
        message = await self.receive()
        if message["type"] == "websocket.disconnect":
            self.state = WebSocketState.DISCONNECTED
            raise RuntimeError("WebSocket disconnected")
        return message.get("bytes", b"")

    def join_room(self, room: str) -> None:
        """Join a room for pub/sub messaging."""
        self.rooms.add(room)
        logger.debug(f"Connection {self.connection_id} joined room {room}")

    def leave_room(self, room: str) -> None:
        """Leave a room."""
        self.rooms.discard(room)
        logger.debug(f"Connection {self.connection_id} left room {room}")

    def _start_heartbeat(self) -> None:
        """Start heartbeat ping/pong."""
        if self._ping_task is None:
            self._ping_task = asyncio.create_task(self._heartbeat_loop())

    def _stop_heartbeat(self) -> None:
        """Stop heartbeat ping/pong."""
        if self._ping_task:
            self._ping_task.cancel()
            self._ping_task = None

    async def _heartbeat_loop(self) -> None:
        """Heartbeat loop for connection health monitoring."""
        while self.state == WebSocketState.CONNECTED:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                if self.state == WebSocketState.CONNECTED:
                    await self.send_ping()
                    # Wait for pong response
                    await asyncio.wait_for(self._wait_for_pong(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning(f"WebSocket {self.connection_id} heartbeat timeout")
                await self.close(1000, "Heartbeat timeout")
                break
            except Exception as e:
                logger.error(f"Heartbeat error for {self.connection_id}: {e}")
                break

    async def _wait_for_pong(self) -> None:
        """Wait for pong response."""
        while self.state == WebSocketState.CONNECTED:
            message = await self.receive()
            if message["type"] == "websocket.disconnect":
                self.state = WebSocketState.DISCONNECTED
                break
            if message.get("type") == "websocket.receive" and "pong" in message:
                self.last_pong = datetime.now()
                break

    async def __aiter__(self) -> AsyncIterator[Any]:
        """Iterate over incoming messages."""
        while self.state == WebSocketState.CONNECTED:
            try:
                message = await self.receive()
                if message["type"] == "websocket.disconnect":
                    self.state = WebSocketState.DISCONNECTED
                    break
                if "text" in message:
                    yield message["text"]
                elif "bytes" in message:
                    yield message["bytes"]
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                break

class WebSocketManager(ABC):
    """Abstract WebSocket manager interface."""
    
    @abstractmethod
    async def add_connection(self, connection: WebSocketConnection) -> None:
        """Add a WebSocket connection."""
        pass
    
    @abstractmethod
    async def remove_connection(self, connection: WebSocketConnection) -> None:
        """Remove a WebSocket connection."""
        pass
    
    @abstractmethod
    async def broadcast(self, message: WebSocketMessage, room: Optional[str] = None) -> None:
        """Broadcast message to all connections or room."""
        pass
    
    @abstractmethod
    async def send_to_connection(self, connection_id: str, message: WebSocketMessage) -> None:
        """Send message to specific connection."""
        pass

class InMemoryWebSocketManager(WebSocketManager):
    """In-memory WebSocket manager implementation."""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.rooms: Dict[str, Set[str]] = {}
        self.message_history: List[WebSocketMessage] = []
        self.max_history = 1000
        logger.debug("Initialized InMemoryWebSocketManager")
    
    async def add_connection(self, connection: WebSocketConnection) -> None:
        """Add a WebSocket connection."""
        self.connections[connection.connection_id] = connection
        logger.info(f"Added connection {connection.connection_id}")
    
    async def remove_connection(self, connection: WebSocketConnection) -> None:
        """Remove a WebSocket connection."""
        connection_id = connection.connection_id
        if connection_id in self.connections:
            del self.connections[connection_id]
            # Remove from all rooms that contain this connection
            for room in list(self.rooms.keys()):
                if connection_id in self.rooms[room]:
                    self._remove_from_room(connection_id, room)
            logger.info(f"Removed connection {connection_id}")
    
    async def broadcast(self, message: WebSocketMessage, room: Optional[str] = None) -> None:
        """Broadcast message to all connections or room."""
        self._add_to_history(message)
        
        if room:
            # Send to room
            room_connections = self.rooms.get(room, set())
            for connection_id in room_connections:
                await self.send_to_connection(connection_id, message)
            logger.debug(f"Broadcasted to room {room}: {len(room_connections)} connections")
        else:
            # Send to all connections
            for connection in self.connections.values():
                if connection.state == WebSocketState.CONNECTED:
                    try:
                        await connection.send_json({
                            "type": message.type,
                            "data": message.data,
                            "timestamp": message.timestamp.isoformat(),
                            "message_id": message.message_id,
                            "sender_id": message.sender_id
                        })
                    except Exception as e:
                        logger.error(f"Error broadcasting to {connection.connection_id}: {e}")
            logger.debug(f"Broadcasted to all: {len(self.connections)} connections")
    
    async def send_to_connection(self, connection_id: str, message: WebSocketMessage) -> None:
        """Send message to specific connection."""
        connection = self.connections.get(connection_id)
        if connection and connection.state == WebSocketState.CONNECTED:
            try:
                await connection.send_json({
                    "type": message.type,
                    "data": message.data,
                    "timestamp": message.timestamp.isoformat(),
                    "message_id": message.message_id,
                    "sender_id": message.sender_id
                })
            except Exception as e:
                logger.error(f"Error sending to {connection_id}: {e}")
        else:
            logger.warning(f"Connection {connection_id} not found or not connected")
    
    def join_room(self, connection_id: str, room: str) -> None:
        """Join connection to a room."""
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(connection_id)
        if connection_id in self.connections:
            self.connections[connection_id].join_room(room)
        logger.debug(f"Connection {connection_id} joined room {room}")
    
    def leave_room(self, connection_id: str, room: str) -> None:
        """Remove connection from a room."""
        self._remove_from_room(connection_id, room)
        if connection_id in self.connections:
            self.connections[connection_id].leave_room(room)
        logger.debug(f"Connection {connection_id} left room {room}")
    
    def _remove_from_room(self, connection_id: str, room: str) -> None:
        """Remove connection from room."""
        if room in self.rooms:
            self.rooms[room].discard(connection_id)
            if not self.rooms[room]:
                del self.rooms[room]
    
    def _add_to_history(self, message: WebSocketMessage) -> None:
        """Add message to history."""
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.connections)
    
    def get_room_connections(self, room: str) -> int:
        """Get number of connections in a room."""
        return len(self.rooms.get(room, set()))
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": len(self.connections),
            "rooms": {room: len(connections) for room, connections in self.rooms.items()},
            "message_history_count": len(self.message_history)
        }

class WebSocketHandler:
    """WebSocket handler with enhanced features."""
    
    def __init__(self, manager: WebSocketManager = None):
        self.manager = manager or InMemoryWebSocketManager()
        self.handlers: Dict[str, Callable] = {}
        logger.debug("Initialized WebSocketHandler")
    
    def on_connect(self, handler: Callable) -> Callable:
        """Decorator for connection event handler."""
        self.handlers["connect"] = handler
        return handler
    
    def on_disconnect(self, handler: Callable) -> Callable:
        """Decorator for disconnection event handler."""
        self.handlers["disconnect"] = handler
        return handler
    
    def on_message(self, message_type: str = "message") -> Callable:
        """Decorator for message event handler."""
        def decorator(handler: Callable) -> Callable:
            self.handlers[message_type] = handler
            return handler
        return decorator
    
    async def handle_connection(self, websocket: WebSocketConnection) -> None:
        """Handle WebSocket connection lifecycle."""
        try:
            # Add to manager
            await self.manager.add_connection(websocket)
            
            # Call connect handler
            if "connect" in self.handlers:
                await self.handlers["connect"](websocket)
            
            # Accept connection
            await websocket.accept()
            
            # Message loop
            async for message_data in websocket:
                try:
                    if isinstance(message_data, str):
                        message = json.loads(message_data)
                    else:
                        message = message_data
                    
                    message_type = message.get("type", "message")
                    
                    if message_type in self.handlers:
                        await self.handlers[message_type](websocket, message)
                    else:
                        # Default message handler
                        await self._handle_default_message(websocket, message)
                        
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {websocket.connection_id}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Call disconnect handler
            if "disconnect" in self.handlers:
                await self.handlers["disconnect"](websocket)
            
            # Remove from manager
            await self.manager.remove_connection(websocket)
    
    async def _handle_default_message(self, websocket: WebSocketConnection, message: Dict) -> None:
        """Handle default message types."""
        message_type = message.get("type")
        
        if message_type == "join_room":
            room = message.get("room")
            if room:
                self.manager.join_room(websocket.connection_id, room)
                await websocket.send_json({
                    "type": "room_joined",
                    "room": room,
                    "success": True
                })
        
        elif message_type == "leave_room":
            room = message.get("room")
            if room:
                self.manager.leave_room(websocket.connection_id, room)
                await websocket.send_json({
                    "type": "room_left",
                    "room": room,
                    "success": True
                })
        
        elif message_type == "broadcast":
            data = message.get("data")
            room = message.get("room")
            if data:
                ws_message = WebSocketMessage(
                    type="broadcast",
                    data=data,
                    sender_id=websocket.connection_id,
                    room=room
                )
                await self.manager.broadcast(ws_message, room)

class WebSocketMiddleware:
    """WebSocket middleware for ASGI applications."""
    
    def __init__(self, app: Any, handler: WebSocketHandler):
        self.app = app
        self.handler = handler
        logger.debug("Initialized WebSocketMiddleware")

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        if scope["type"] == "websocket":
            websocket = WebSocketConnection(scope, receive, send)
            await self.handler.handle_connection(websocket)
        else:
            await self.app(scope, receive, send)
