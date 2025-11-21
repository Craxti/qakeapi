"""Enhanced WebSocket Example with broadcast, pub/sub, and reconnect support."""

import asyncio
import json
import logging
from datetime import datetime
from qakeapi import Application
from qakeapi.core.websockets import (
    WebSocketHandler, 
    InMemoryWebSocketManager, 
    WebSocketMessage,
    WebSocketMiddleware,
    WebSocketConnection
)
from qakeapi.core.responses import Response
from qakeapi.security.websocket_auth import (
    AuthConfig, AuthStatus, JWTAuthenticator, WebSocketAuthMiddleware, WebSocketAuthHandler
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create application
app = Application()

# Create WebSocket manager and handler
ws_manager = InMemoryWebSocketManager()
ws_handler = WebSocketHandler(ws_manager)

# --- WebSocket Authentication Setup ---
AUTH_SECRET = "supersecretkey123"
auth_config = AuthConfig(secret_key=AUTH_SECRET)
jwt_authenticator = JWTAuthenticator(auth_config)
ws_auth_middleware = WebSocketAuthMiddleware(jwt_authenticator, auth_config)
ws_auth_handler = WebSocketAuthHandler(ws_auth_middleware)

# WebSocket маршрут обрабатывается напрямую через @app.websocket("/ws")

# WebSocket event handlers
# WebSocket event handlers moved to inline processing in websocket_endpoint

async def handle_chat_message(websocket, message):
    """Handle chat messages."""
    data = message.get("data", {})
    room = data.get("room", "general")
    
    # Create chat message
    chat_message = WebSocketMessage(
        type="chat",
        data={
            "message": data.get("message", ""),
            "sender_id": websocket.connection_id,
            "sender_name": data.get("sender_name", f"User-{websocket.connection_id[:8]}"),
            "room": room,
            "timestamp": datetime.now().isoformat()
        },
        sender_id=websocket.connection_id,
        room=room
    )
    
    # Broadcast to room
    await ws_manager.broadcast(chat_message, room)
    
    # Send confirmation
    await websocket.send_json({
        "type": "message_sent",
        "data": {
            "message_id": chat_message.message_id,
            "timestamp": chat_message.timestamp.isoformat()
        }
    })

async def handle_join_room(websocket, message):
    """Handle room join requests."""
    data = message.get("data", {})
    room = data.get("room", "general")
    
    # Join room
    ws_manager.join_room(websocket.connection_id, room)
    
    # Send confirmation
    await websocket.send_json({
        "type": "room_joined",
        "data": {
            "room": room,
            "connection_id": websocket.connection_id,
            "timestamp": datetime.now().isoformat()
        }
    })
    
    # Broadcast user joined message to room
    join_message = WebSocketMessage(
        type="user_joined",
        data={
            "connection_id": websocket.connection_id,
            "room": room,
            "timestamp": datetime.now().isoformat()
        },
        room=room
    )
    await ws_manager.broadcast(join_message, room)

async def handle_leave_room(websocket, message):
    """Handle room leave requests."""
    data = message.get("data", {})
    room = data.get("room", "general")
    
    # Leave room
    ws_manager.leave_room(websocket.connection_id, room)
    
    # Send confirmation
    await websocket.send_json({
        "type": "room_left",
        "data": {
            "room": room,
            "connection_id": websocket.connection_id,
            "timestamp": datetime.now().isoformat()
        }
    })
    
    # Broadcast user left message to room
    leave_message = WebSocketMessage(
        type="user_left",
        data={
            "connection_id": websocket.connection_id,
            "room": room,
            "timestamp": datetime.now().isoformat()
        },
        room=room
    )
    await ws_manager.broadcast(leave_message, room)

async def handle_private_message(websocket, message):
    """Handle private messages."""
    data = message.get("data", {})
    target_id = data.get("target_id")
    message_text = data.get("message", "")
    
    if target_id:
        # Create private message
        private_message = WebSocketMessage(
            type="private_message",
            data={
                "message": message_text,
                "sender_id": websocket.connection_id,
                "sender_name": data.get("sender_name", f"User-{websocket.connection_id[:8]}"),
                "timestamp": datetime.now().isoformat()
            },
            sender_id=websocket.connection_id
        )
        
        # Send to target
        await ws_manager.send_to_connection(target_id, private_message)
        
        # Send confirmation to sender
        await websocket.send_json({
            "type": "private_message_sent",
            "data": {
                "target_id": target_id,
                "message_id": private_message.message_id,
                "timestamp": private_message.timestamp.isoformat()
            }
        })
    else:
        await websocket.send_json({
            "type": "error",
            "data": {
                "message": "Target ID is required for private messages",
                "timestamp": datetime.now().isoformat()
            }
        })

async def handle_get_connections(websocket, message):
    """Handle connection info requests."""
    info = ws_manager.get_connection_info()
    await websocket.send_json({
        "type": "connections_info",
        "data": info
    })

async def handle_auth(websocket, message):
    """Handle authentication messages."""
    try:
        auth_data = message.get("data", {})
        result = await jwt_authenticator.authenticate(websocket, auth_data)
        
        if result.status == AuthStatus.AUTHENTICATED:
            # Добавляем в аутентифицированные соединения
            ws_auth_middleware._authenticated_connections[websocket.connection_id] = result
            
            await websocket.send_json({
                "type": "auth_success",
                "data": {
                    "user_id": result.user_id,
                    "user_data": result.user_data,
                    "expires_at": result.expires_at.isoformat() if result.expires_at else None,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Send current connection info after successful auth
            info = ws_manager.get_connection_info()
            await websocket.send_json({
                "type": "connection_info",
                "data": info
            })
            
        else:
            await websocket.send_json({
                "type": "auth_error",
                "data": {
                    "error": result.error_message,
                    "status": result.status.value,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        await websocket.send_json({
            "type": "auth_error",
            "data": {
                "error": "Authentication failed",
                "status": "invalid",
                "timestamp": datetime.now().isoformat()
            }
        })

async def handle_ping(websocket, message):
    """Handle ping messages."""
    await websocket.send_json({
        "type": "pong",
        "data": {
            "timestamp": datetime.now().isoformat(),
            "echo": message.get("data", {}).get("echo", "")
        }
    })

# HTTP routes
@app.get("/")
async def index(request):
    """Main page with WebSocket client."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enhanced WebSocket Chat</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .chat-area { height: 400px; border: 1px solid #ccc; overflow-y: scroll; padding: 10px; margin: 10px 0; }
            .input-area { display: flex; gap: 10px; margin: 10px 0; }
            .input-area input, .input-area button { padding: 8px; }
            .input-area input { flex: 1; }
            .status { padding: 10px; background: #f0f0f0; margin: 10px 0; }
            .message { margin: 5px 0; padding: 5px; border-radius: 5px; }
            .message.sent { background: #e3f2fd; }
            .message.received { background: #f3e5f5; }
            .message.system { background: #fff3e0; }
            .rooms { display: flex; gap: 10px; margin: 10px 0; }
            .room { padding: 5px 10px; background: #ddd; border-radius: 5px; cursor: pointer; }
            .room.active { background: #4caf50; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Enhanced WebSocket Chat</h1>
            
            <div class="status" id="status">Connecting...</div>
            
            <div class="rooms">
                <div class="room active" data-room="general">General</div>
                <div class="room" data-room="tech">Tech</div>
                <div class="room" data-room="random">Random</div>
            </div>
            
            <div class="chat-area" id="chatArea"></div>
            
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="Type your message..." />
                <button onclick="sendMessage()">Send</button>
                <button onclick="sendPing()">Ping</button>
            </div>
            
            <div class="input-area">
                <input type="text" id="privateInput" placeholder="Private message (target_id: message)" />
                <button onclick="sendPrivateMessage()">Send Private</button>
            </div>
            
            <div class="input-area">
                <input type="text" id="usernameInput" placeholder="Your username" />
                <button onclick="setUsername()">Set Username</button>
            </div>
        </div>

        <script>
            let ws;
            let currentRoom = 'general';
            let username = '';
            let connectionId = '';

            function connect() {
                ws = new WebSocket('ws://localhost:8021/ws');
                
                ws.onopen = function() {
                    document.getElementById('status').textContent = 'Connected';
                    document.getElementById('status').style.background = '#c8e6c9';
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };
                
                ws.onclose = function() {
                    document.getElementById('status').textContent = 'Disconnected - Reconnecting...';
                    document.getElementById('status').style.background = '#ffcdd2';
                    setTimeout(connect, 1000);
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }

            function handleMessage(data) {
                const chatArea = document.getElementById('chatArea');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message';
                
                switch(data.type) {
                    case 'welcome':
                        connectionId = data.data.connection_id;
                        messageDiv.className += ' system';
                        messageDiv.textContent = `Welcome! Your ID: ${connectionId}`;
                        break;
                        
                    case 'chat':
                        messageDiv.className += data.data.sender_id === connectionId ? ' sent' : ' received';
                        messageDiv.textContent = `${data.data.sender_name}: ${data.data.message}`;
                        break;
                        
                    case 'user_joined':
                        messageDiv.className += ' system';
                        messageDiv.textContent = `User joined room: ${data.data.connection_id}`;
                        break;
                        
                    case 'user_left':
                        messageDiv.className += ' system';
                        messageDiv.textContent = `User left: ${data.data.connection_id}`;
                        break;
                        
                    case 'private_message':
                        messageDiv.className += ' received';
                        messageDiv.textContent = `[PRIVATE] ${data.data.sender_name}: ${data.data.message}`;
                        break;
                        
                    case 'pong':
                        messageDiv.className += ' system';
                        messageDiv.textContent = `Pong received: ${data.data.echo}`;
                        break;
                        
                    default:
                        messageDiv.textContent = JSON.stringify(data);
                }
                
                chatArea.appendChild(messageDiv);
                chatArea.scrollTop = chatArea.scrollHeight;
            }

            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                
                if (message && ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'chat',
                        data: {
                            message: message,
                            room: currentRoom,
                            sender_name: username || `User-${connectionId?.slice(0, 8)}`
                        }
                    }));
                    input.value = '';
                }
            }

            function sendPrivateMessage() {
                const input = document.getElementById('privateInput');
                const text = input.value.trim();
                
                if (text && ws && ws.readyState === WebSocket.OPEN) {
                    const parts = text.split(':');
                    if (parts.length >= 2) {
                        const targetId = parts[0].trim();
                        const message = parts.slice(1).join(':').trim();
                        
                        ws.send(JSON.stringify({
                            type: 'private_message',
                            data: {
                                target_id: targetId,
                                message: message,
                                sender_name: username || `User-${connectionId?.slice(0, 8)}`
                            }
                        }));
                        input.value = '';
                    }
                }
            }

            function sendPing() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'ping',
                        data: {
                            echo: 'Hello from client!'
                        }
                    }));
                }
            }

            function setUsername() {
                const input = document.getElementById('usernameInput');
                username = input.value.trim();
                if (username) {
                    input.value = '';
                    document.getElementById('status').textContent = `Connected as: ${username}`;
                }
            }

            // Room switching
            document.querySelectorAll('.room').forEach(room => {
                room.addEventListener('click', function() {
                    const roomName = this.dataset.room;
                    
                    // Leave current room
                    if (currentRoom && ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            type: 'leave_room',
                            data: { room: currentRoom }
                        }));
                    }
                    
                    // Join new room
                    currentRoom = roomName;
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            type: 'join_room',
                            data: { room: roomName }
                        }));
                    }
                    
                    // Update UI
                    document.querySelectorAll('.room').forEach(r => r.classList.remove('active'));
                    this.classList.add('active');
                });
            });

            // Enter key handlers
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });

            document.getElementById('privateInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendPrivateMessage();
            });

            document.getElementById('usernameInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') setUsername();
            });

            // Connect on page load
            connect();
        </script>
    </body>
    </html>
    """
    return Response.html(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint with authentication."""
    try:
        # Accept connection
        await websocket.accept()
        
        # Add to manager
        await ws_manager.add_connection(websocket)
        
        # Send welcome message
        await websocket.send_json({
            "type": "welcome",
            "data": {
                "message": "Welcome to Enhanced WebSocket Chat! Please authenticate.",
                "connection_id": websocket.connection_id,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Send authentication required message
        await websocket.send_json({
            "type": "auth_required",
            "data": {
                "message": "Authentication required. Send auth message with token.",
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Message loop
        async for message_data in websocket:
            try:
                if isinstance(message_data, str):
                    message = json.loads(message_data)
                else:
                    message = message_data
                
                message_type = message.get("type", "message")
                
                # Handle authentication
                if message_type == "auth":
                    await handle_auth(websocket, message)
                # Handle other messages with authentication check
                elif message_type in ["chat", "private_message"]:
                    if not ws_auth_middleware.is_authenticated(websocket.connection_id):
                        await websocket.send_json({
                            "type": "error",
                            "data": {
                                "error": "Authentication required",
                                "code": "AUTH_REQUIRED"
                            }
                        })
                    else:
                        if message_type == "chat":
                            await handle_chat_message(websocket, message)
                        elif message_type == "private_message":
                            await handle_private_message(websocket, message)
                # Handle non-protected messages
                elif message_type == "join_room":
                    await handle_join_room(websocket, message)
                elif message_type == "leave_room":
                    await handle_leave_room(websocket, message)
                elif message_type == "get_connections":
                    await handle_get_connections(websocket, message)
                elif message_type == "ping":
                    await handle_ping(websocket, message)
                else:
                    # Default message handler
                    await websocket.send_json({
                        "type": "error",
                        "data": {
                            "error": f"Unknown message type: {message_type}",
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                    
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {websocket.connection_id}")
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "error": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    }
                })
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "error": "Internal server error",
                        "timestamp": datetime.now().isoformat()
                    }
                })
                    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Remove from manager
        await ws_manager.remove_connection(websocket)

@app.get("/api/connections")
async def get_connections(request):
    """Get connection statistics."""
    try:
        info = ws_manager.get_connection_info()
        return Response.json(info)
    except Exception as e:
        return Response.json({"error": str(e)}, status_code=500)

@app.get("/api/broadcast")
async def broadcast_message(request, message: str = "Hello from server!"):
    """Broadcast a message to all connected clients."""
    try:
        broadcast_msg = WebSocketMessage(
            type="broadcast",
            data={
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        )
        await ws_manager.broadcast(broadcast_msg)
        return Response.json({
            "message": "Broadcast sent",
            "recipients": ws_manager.get_connection_count()
        })
    except Exception as e:
        return Response.json({"error": str(e)}, status_code=500)

@app.get("/api/rooms")
async def get_rooms(request):
    """Get room information."""
    try:
        info = ws_manager.get_connection_info()
        return Response.json({
            "rooms": info.get("rooms", {}),
            "total_connections": info.get("total_connections", 0)
        })
    except Exception as e:
        return Response.json({"error": str(e)}, status_code=500)

@app.get("/api/generate-token")
async def generate_token(request):
    user_data = {"user_id": "demo_user", "name": "Demo User"}
    token = await jwt_authenticator.create_token(user_data)
    return {"token": token}

if __name__ == "__main__":
    print("🚀 Starting Enhanced WebSocket Example...")
    print("📖 Available endpoints:")
    print("  - / - WebSocket chat interface")
    print("  - /ws - WebSocket endpoint")
    print("  - /api/connections - Connection statistics")
    print("  - /api/broadcast - Broadcast message")
    print("  - /api/rooms - Room information")
    print("  - /api/generate-token - Generate a test token")
    print("  - /docs - API documentation")
    
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8021) 