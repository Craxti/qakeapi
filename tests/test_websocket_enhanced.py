"""Tests for enhanced WebSocket system."""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from qakeapi.core.websockets import (
    InMemoryWebSocketManager,
    WebSocketConnection,
    WebSocketHandler,
    WebSocketManager,
    WebSocketMessage,
    WebSocketMiddleware,
    WebSocketState,
)


class TestWebSocketConnection:
    """Test WebSocket connection functionality."""

    def test_connection_creation(self):
        """Test WebSocket connection creation."""
        scope = {"client": ("127.0.0.1", 12345), "path": "/ws"}
        receive = Mock()
        send = Mock()

        connection = WebSocketConnection(scope, receive, send)

        assert connection.state == WebSocketState.CONNECTING
        assert connection.client == ("127.0.0.1", 12345)
        assert connection.path == "/ws"
        assert connection.connection_id is not None
        assert len(connection.rooms) == 0

    def test_connection_with_custom_id(self):
        """Test WebSocket connection with custom ID."""
        scope = {"client": ("127.0.0.1", 12345)}
        receive = Mock()
        send = Mock()

        connection = WebSocketConnection(scope, receive, send, "custom-id")

        assert connection.connection_id == "custom-id"

    def test_join_and_leave_room(self):
        """Test joining and leaving rooms."""
        scope = {"client": ("127.0.0.1", 12345)}
        receive = Mock()
        send = Mock()

        connection = WebSocketConnection(scope, receive, send)

        # Join room
        connection.join_room("test-room")
        assert "test-room" in connection.rooms

        # Leave room
        connection.leave_room("test-room")
        assert "test-room" not in connection.rooms

    @pytest.mark.asyncio
    async def test_connection_accept(self):
        """Test connection acceptance."""
        scope = {"client": ("127.0.0.1", 12345)}
        receive = Mock()
        send = AsyncMock()

        connection = WebSocketConnection(scope, receive, send)

        await connection.accept()

        assert connection.state == WebSocketState.CONNECTED
        send.assert_called_once_with({"type": "websocket.accept", "subprotocol": None})

    @pytest.mark.asyncio
    async def test_connection_close(self):
        """Test connection closing."""
        scope = {"client": ("127.0.0.1", 12345)}
        receive = Mock()
        send = AsyncMock()

        connection = WebSocketConnection(scope, receive, send)
        connection.state = WebSocketState.CONNECTED

        await connection.close(1000, "Test close")

        assert connection.state == WebSocketState.DISCONNECTED
        send.assert_called_once_with(
            {"type": "websocket.close", "code": 1000, "reason": "Test close"}
        )

    @pytest.mark.asyncio
    async def test_send_json(self):
        """Test sending JSON data."""
        scope = {"client": ("127.0.0.1", 12345)}
        receive = Mock()
        send = AsyncMock()

        connection = WebSocketConnection(scope, receive, send)
        connection.state = WebSocketState.CONNECTED

        data = {"message": "test", "timestamp": "2024-01-01"}
        await connection.send_json(data)

        send.assert_called_once_with(
            {"type": "websocket.send", "text": json.dumps(data)}
        )

    @pytest.mark.asyncio
    async def test_send_ping(self):
        """Test sending ping."""
        scope = {"client": ("127.0.0.1", 12345)}
        receive = Mock()
        send = AsyncMock()

        connection = WebSocketConnection(scope, receive, send)
        connection.state = WebSocketState.CONNECTED

        await connection.send_ping(b"test")

        assert connection.last_ping is not None
        send.assert_called_once_with(
            {"type": "websocket.send", "bytes": b"test", "ping": True}
        )


class TestWebSocketMessage:
    """Test WebSocket message functionality."""

    def test_message_creation(self):
        """Test WebSocket message creation."""
        message = WebSocketMessage(
            type="chat", data={"text": "Hello"}, sender_id="user123", room="general"
        )

        assert message.type == "chat"
        assert message.data["text"] == "Hello"
        assert message.sender_id == "user123"
        assert message.room == "general"
        assert message.message_id is not None
        assert message.timestamp is not None

    def test_message_with_defaults(self):
        """Test WebSocket message with default values."""
        message = WebSocketMessage(type="ping", data="test")

        assert message.type == "ping"
        assert message.data == "test"
        assert message.sender_id is None
        assert message.room is None
        assert message.message_id is not None
        assert message.timestamp is not None


class TestInMemoryWebSocketManager:
    """Test in-memory WebSocket manager."""

    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = InMemoryWebSocketManager()

        assert len(manager.connections) == 0
        assert len(manager.rooms) == 0
        assert len(manager.message_history) == 0
        assert manager.max_history == 1000

    @pytest.mark.asyncio
    async def test_add_and_remove_connection(self):
        """Test adding and removing connections."""
        manager = InMemoryWebSocketManager()

        # Create mock connection
        connection = Mock()
        connection.connection_id = "test-connection"
        connection.rooms = set()

        # Add connection
        await manager.add_connection(connection)
        assert "test-connection" in manager.connections
        assert manager.get_connection_count() == 1

        # Remove connection
        await manager.remove_connection(connection)
        assert "test-connection" not in manager.connections
        assert manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_join_and_leave_room(self):
        """Test joining and leaving rooms."""
        manager = InMemoryWebSocketManager()

        # Create mock connection
        connection = Mock()
        connection.connection_id = "test-connection"
        connection.rooms = set()
        connection.join_room = Mock()
        connection.leave_room = Mock()

        # Add connection
        await manager.add_connection(connection)

        # Join room
        manager.join_room("test-connection", "test-room")
        assert "test-room" in manager.rooms
        assert "test-connection" in manager.rooms["test-room"]
        assert manager.get_room_connections("test-room") == 1
        connection.join_room.assert_called_once_with("test-room")

        # Leave room
        manager.leave_room("test-connection", "test-room")
        assert "test-room" not in manager.rooms
        assert manager.get_room_connections("test-room") == 0
        connection.leave_room.assert_called_once_with("test-room")

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self):
        """Test broadcasting to all connections."""
        manager = InMemoryWebSocketManager()

        # Create mock connections
        connection1 = Mock()
        connection1.connection_id = "conn1"
        connection1.state = WebSocketState.CONNECTED
        connection1.send_json = AsyncMock()

        connection2 = Mock()
        connection2.connection_id = "conn2"
        connection2.state = WebSocketState.CONNECTED
        connection2.send_json = AsyncMock()

        # Add connections
        await manager.add_connection(connection1)
        await manager.add_connection(connection2)

        # Create message
        message = WebSocketMessage(
            type="broadcast", data={"text": "Hello everyone"}, sender_id="server"
        )

        # Broadcast
        await manager.broadcast(message)

        # Check that both connections received the message
        assert connection1.send_json.call_count == 1
        assert connection2.send_json.call_count == 1

        # Check message history
        assert len(manager.message_history) == 1
        assert manager.message_history[0] == message

    @pytest.mark.asyncio
    async def test_broadcast_to_room(self):
        """Test broadcasting to specific room."""
        manager = InMemoryWebSocketManager()

        # Create mock connections
        connection1 = Mock()
        connection1.connection_id = "conn1"
        connection1.state = WebSocketState.CONNECTED
        connection1.send_json = AsyncMock()

        connection2 = Mock()
        connection2.connection_id = "conn2"
        connection2.state = WebSocketState.CONNECTED
        connection2.send_json = AsyncMock()

        # Add connections
        await manager.add_connection(connection1)
        await manager.add_connection(connection2)

        # Join room
        manager.join_room("conn1", "test-room")

        # Create message
        message = WebSocketMessage(
            type="chat",
            data={"text": "Hello room"},
            sender_id="user1",
            room="test-room",
        )

        # Broadcast to room
        await manager.broadcast(message, "test-room")

        # Check that only room member received the message
        assert connection1.send_json.call_count == 1
        assert connection2.send_json.call_count == 0

    @pytest.mark.asyncio
    async def test_send_to_connection(self):
        """Test sending to specific connection."""
        manager = InMemoryWebSocketManager()

        # Create mock connection
        connection = Mock()
        connection.connection_id = "test-connection"
        connection.state = WebSocketState.CONNECTED
        connection.send_json = AsyncMock()

        # Add connection
        await manager.add_connection(connection)

        # Create message
        message = WebSocketMessage(
            type="private", data={"text": "Private message"}, sender_id="user1"
        )

        # Send to connection
        await manager.send_to_connection("test-connection", message)

        # Check that connection received the message
        assert connection.send_json.call_count == 1

    def test_get_connection_info(self):
        """Test getting connection information."""
        manager = InMemoryWebSocketManager()

        # Add some rooms
        manager.rooms["room1"] = {"conn1", "conn2"}
        manager.rooms["room2"] = {"conn3"}

        # Add some message history
        message = WebSocketMessage(type="test", data="test")
        manager.message_history.append(message)

        info = manager.get_connection_info()

        assert info["total_connections"] == 0
        assert info["rooms"]["room1"] == 2
        assert info["rooms"]["room2"] == 1
        assert info["message_history_count"] == 1


class TestWebSocketHandler:
    """Test WebSocket handler functionality."""

    def test_handler_initialization(self):
        """Test handler initialization."""
        manager = InMemoryWebSocketManager()
        handler = WebSocketHandler(manager)

        assert handler.manager == manager
        assert len(handler.handlers) == 0

    def test_connect_decorator(self):
        """Test connect event decorator."""
        handler = WebSocketHandler()

        @handler.on_connect
        async def connect_handler(websocket):
            pass

        assert "connect" in handler.handlers
        assert handler.handlers["connect"] == connect_handler

    def test_disconnect_decorator(self):
        """Test disconnect event decorator."""
        handler = WebSocketHandler()

        @handler.on_disconnect
        async def disconnect_handler(websocket):
            pass

        assert "disconnect" in handler.handlers
        assert handler.handlers["disconnect"] == disconnect_handler

    def test_message_decorator(self):
        """Test message event decorator."""
        handler = WebSocketHandler()

        @handler.on_message("chat")
        async def chat_handler(websocket, message):
            pass

        assert "chat" in handler.handlers
        assert handler.handlers["chat"] == chat_handler

    @pytest.mark.asyncio
    async def test_handle_connection_lifecycle(self):
        """Test connection lifecycle handling."""
        manager = InMemoryWebSocketManager()
        handler = WebSocketHandler(manager)

        # Mock handlers
        connect_called = False
        disconnect_called = False

        @handler.on_connect
        async def connect_handler(websocket):
            nonlocal connect_called
            connect_called = True

        @handler.on_disconnect
        async def disconnect_handler(websocket):
            nonlocal disconnect_called
            disconnect_called = True

        # Create mock websocket
        websocket = Mock()
        websocket.connection_id = "test-connection"
        websocket.rooms = set()
        websocket.accept = AsyncMock()

        # Create a proper async iterator
        async def async_iter():
            yield {"type": "websocket.disconnect"}

        websocket.__aiter__ = lambda: async_iter()

        # Handle connection
        await handler.handle_connection(websocket)

        # Check that handlers were called
        assert connect_called
        assert disconnect_called
        assert websocket.accept.called

    @pytest.mark.asyncio
    async def test_handle_default_messages(self):
        """Test handling default message types."""
        manager = InMemoryWebSocketManager()
        handler = WebSocketHandler(manager)

        # Create mock websocket
        websocket = Mock()
        websocket.connection_id = "test-connection"
        websocket.rooms = set()
        websocket.send_json = AsyncMock()

        # Add connection to manager
        await manager.add_connection(websocket)

        # Test join room message
        join_message = {"type": "join_room", "room": "test-room"}

        await handler._handle_default_message(websocket, join_message)

        # Check that room join was processed
        assert "test-room" in manager.rooms
        assert "test-connection" in manager.rooms["test-room"]
        assert websocket.send_json.called

    @pytest.mark.asyncio
    async def test_handle_broadcast_message(self):
        """Test handling broadcast messages."""
        manager = InMemoryWebSocketManager()
        handler = WebSocketHandler(manager)

        # Create mock websocket
        websocket = Mock()
        websocket.connection_id = "test-connection"
        websocket.send_json = AsyncMock()

        # Test broadcast message
        broadcast_message = {
            "type": "broadcast",
            "data": {"message": "Hello"},
            "room": "test-room",
        }

        await handler._handle_default_message(websocket, broadcast_message)

        # Check that broadcast was processed
        assert len(manager.message_history) == 1
        assert manager.message_history[0].type == "broadcast"


class TestWebSocketMiddleware:
    """Test WebSocket middleware."""

    @pytest.mark.asyncio
    async def test_middleware_websocket_handling(self):
        """Test middleware WebSocket handling."""
        app = Mock()
        handler = WebSocketHandler()
        middleware = WebSocketMiddleware(app, handler)

        # Mock scope and functions
        scope = {"type": "websocket", "client": ("127.0.0.1", 12345)}
        receive = Mock()
        send = Mock()

        # Mock handler method
        handler.handle_connection = AsyncMock()

        # Call middleware
        await middleware(scope, receive, send)

        # Check that handler was called
        assert handler.handle_connection.called

    @pytest.mark.asyncio
    async def test_middleware_http_passthrough(self):
        """Test middleware HTTP passthrough."""
        app = AsyncMock()
        handler = WebSocketHandler()
        middleware = WebSocketMiddleware(app, handler)

        # Mock scope and functions
        scope = {"type": "http", "client": ("127.0.0.1", 12345)}
        receive = Mock()
        send = Mock()

        # Call middleware
        await middleware(scope, receive, send)

        # Check that app was called
        app.assert_called_once_with(scope, receive, send)


class TestIntegration:
    """Integration tests for WebSocket system."""

    @pytest.mark.asyncio
    async def test_full_websocket_workflow(self):
        """Test complete WebSocket workflow."""
        # Setup
        manager = InMemoryWebSocketManager()
        handler = WebSocketHandler(manager)

        # Create mock connections
        connection1 = Mock()
        connection1.connection_id = "conn1"
        connection1.state = WebSocketState.CONNECTED
        connection1.send_json = AsyncMock()
        connection1.rooms = set()

        connection2 = Mock()
        connection2.connection_id = "conn2"
        connection2.state = WebSocketState.CONNECTED
        connection2.send_json = AsyncMock()
        connection2.rooms = set()

        # Add connections
        await manager.add_connection(connection1)
        await manager.add_connection(connection2)

        # Join room
        manager.join_room("conn1", "test-room")
        manager.join_room("conn2", "test-room")

        # Create and broadcast message
        message = WebSocketMessage(
            type="chat",
            data={"text": "Hello room"},
            sender_id="conn1",
            room="test-room",
        )

        await manager.broadcast(message, "test-room")

        # Verify both connections received the message
        assert connection1.send_json.call_count == 1
        assert connection2.send_json.call_count == 1

        # Verify message history
        assert len(manager.message_history) == 1
        assert manager.message_history[0] == message

    @pytest.mark.asyncio
    async def test_room_management(self):
        """Test room management functionality."""
        manager = InMemoryWebSocketManager()

        # Create connections
        connections = []
        for i in range(3):
            conn = Mock()
            conn.connection_id = f"conn{i}"
            conn.state = WebSocketState.CONNECTED
            conn.send_json = AsyncMock()
            conn.rooms = set()
            conn.join_room = Mock()
            conn.leave_room = Mock()
            connections.append(conn)
            await manager.add_connection(conn)

        # Join rooms
        manager.join_room("conn0", "room1")
        manager.join_room("conn1", "room1")
        manager.join_room("conn1", "room2")
        manager.join_room("conn2", "room2")

        # Check room counts
        assert manager.get_room_connections("room1") == 2
        assert manager.get_room_connections("room2") == 2

        # Leave room
        manager.leave_room("conn1", "room1")
        assert manager.get_room_connections("room1") == 1
        assert manager.get_room_connections("room2") == 2

        # Debug: print room state before removal
        print(f"Before removal - room2: {manager.rooms.get('room2', set())}")

        # Remove connection
        await manager.remove_connection(connections[2])

        # Debug: print room state after removal
        print(f"After removal - room2: {manager.rooms.get('room2', set())}")

        assert manager.get_room_connections("room2") == 1
