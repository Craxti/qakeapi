# WebSocket Support

QakeAPI includes built-in WebSocket support for real-time communication.

**Why QakeAPI WebSockets:** Native ASGI — no `websockets` or `python-socketio` package. `iter_json()` helper for clean message loops. Benchmarks: ~1.2K connections/sec vs Flask-SocketIO ~450. See [benchmarks](benchmarks.md).

## Basic WebSocket

Create a WebSocket endpoint:

```python
from qakeapi import QakeAPI
from qakeapi.core.websocket import WebSocket

app = QakeAPI()

@app.websocket("/ws")
async def websocket_handler(websocket: WebSocket):
    """Basic WebSocket handler."""
    await websocket.accept()
    await websocket.send_json({"message": "Connected"})
    
    async for message in websocket.iter_json():
        await websocket.send_json({"echo": message})
```

## WebSocket with Path Parameters

Extract path parameters:

```python
@app.websocket("/ws/{room}")
async def room_handler(websocket: WebSocket, room: str):
    """WebSocket with path parameter."""
    await websocket.accept()
    await websocket.send_json({"message": f"Welcome to {room}!"})
    
    async for message in websocket.iter_json():
        await websocket.send_json({
            "room": room,
            "message": message
        })
```

## Sending Messages

Send different message types:

```python
@app.websocket("/ws")
async def chat_handler(websocket: WebSocket):
    await websocket.accept()
    
    # Send JSON
    await websocket.send_json({"type": "welcome", "message": "Hello"})
    
    # Send text
    await websocket.send_text("Text message")
    
    # Send bytes
    await websocket.send_bytes(b"Binary data")
```

## Receiving Messages

Receive different message types:

```python
@app.websocket("/ws")
async def handler(websocket: WebSocket):
    await websocket.accept()
    
    # Receive JSON
    async for message in websocket.iter_json():
        await websocket.send_json({"echo": message})
    
    # Receive text
    async for message in websocket.iter_text():
        await websocket.send_text(f"Echo: {message}")
    
    # Receive bytes
    async for message in websocket.iter_bytes():
        await websocket.send_bytes(message)
```

## Error Handling

Handle WebSocket errors:

```python
@app.websocket("/ws")
async def handler(websocket: WebSocket):
    try:
        await websocket.accept()
        
        async for message in websocket.iter_json():
            try:
                # Process message
                await process_message(message)
                await websocket.send_json({"status": "ok"})
            except ValueError as e:
                await websocket.send_json({"error": str(e)})
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
```

## Broadcasting

Broadcast messages to multiple clients:

```python
# Store connected clients
clients = set()

@app.websocket("/ws")
async def broadcast_handler(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    
    try:
        async for message in websocket.iter_json():
            # Broadcast to all clients
            for client in clients:
                try:
                    await client.send_json(message)
                except Exception:
                    clients.remove(client)
    finally:
        clients.remove(websocket)
        await websocket.close()
```

## Room-based Chat

Implement room-based chat:

```python
rooms = defaultdict(set)

@app.websocket("/ws/{room}")
async def room_chat(websocket: WebSocket, room: str):
    await websocket.accept()
    rooms[room].add(websocket)
    
    try:
        async for message in websocket.iter_json():
            # Broadcast to room
            for client in rooms[room]:
                if client != websocket:
                    try:
                        await client.send_json(message)
                    except Exception:
                        rooms[room].remove(client)
    finally:
        rooms[room].remove(websocket)
        await websocket.close()
```

## Connection Status

Check connection status:

```python
@app.websocket("/ws")
async def handler(websocket: WebSocket):
    await websocket.accept()
    
    # Check if connected
    if websocket.client_state == "CONNECTED":
        await websocket.send_json({"status": "connected"})
    
    async for message in websocket.iter_json():
        # Process message
        pass
```

## Use Cases

### 1. Real-time Notifications

```python
@app.websocket("/ws/notifications/{user_id}")
async def notifications(websocket: WebSocket, user_id: int):
    await websocket.accept()
    
    # Send notifications as they arrive
    async for notification in get_notifications(user_id):
        await websocket.send_json(notification)
```

### 2. Live Updates

```python
@app.websocket("/ws/updates")
async def live_updates(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        updates = await get_updates()
        await websocket.send_json(updates)
        await asyncio.sleep(1)
```

### 3. Chat Application

```python
@app.websocket("/ws/chat/{room}")
async def chat(websocket: WebSocket, room: str):
    await websocket.accept()
    
    async for message in websocket.iter_json():
        # Save message
        await save_message(room, message)
        
        # Broadcast to room
        await broadcast_to_room(room, message)
```

## Best Practices

1. **Handle disconnections** - clients can disconnect at any time
2. **Clean up resources** - remove clients from sets/lists on disconnect
3. **Handle errors** - wrap operations in try/except
4. **Use async** - WebSocket operations are async
5. **Close connections** - always close WebSocket in finally block


