#!/usr/bin/env python3
"""
WebSocket Clustered Application Example

Demonstrates WebSocket clustering with Redis pub/sub for distributed messaging.
Run multiple instances on different ports to test clustering.

Usage:
    python websocket_clustered_app.py --port 8021 --node-id node1
    python websocket_clustered_app.py --port 8022 --node-id node2
"""

import asyncio
import json
import logging
import argparse
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# QakeAPI imports
from qakeapi import Application
from qakeapi.core.websockets import (
    WebSocketConnection, WebSocketMessage, InMemoryWebSocketManager
)
from qakeapi.core.responses import Response
from qakeapi.core.clustering import create_clustered_manager
from qakeapi.security.websocket_auth import (
    AuthConfig, AuthStatus, JWTAuthenticator, WebSocketAuthMiddleware, WebSocketAuthHandler
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application setup
app = Application("WebSocket Clustered Example")

# Configuration
NODE_ID = os.getenv("NODE_ID", "node1")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
PORT = int(os.getenv("PORT", 8021))

# WebSocket managers
local_ws_manager = InMemoryWebSocketManager()
clustered_ws_manager = None

# Authentication setup
auth_config = AuthConfig(
    secret_key="your-secret-key-for-clustering",
    algorithm="HS256",
    token_expiry=timedelta(minutes=60),
    require_auth=True,
    max_auth_attempts=3
)

jwt_authenticator = JWTAuthenticator(auth_config)
ws_auth_middleware = WebSocketAuthMiddleware(jwt_authenticator, auth_config)
ws_auth_handler = WebSocketAuthHandler(ws_auth_middleware)

# Connection tracking
active_connections: Dict[str, WebSocketConnection] = {}


async def setup_clustering():
    """Setup clustering infrastructure."""
    global clustered_ws_manager
    
    try:
        # Create clustered manager
        clustered_ws_manager = create_clustered_manager(
            node_id=NODE_ID,
            redis_url=REDIS_URL,
            local_manager=local_ws_manager
        )
        
        # Start cluster node
        await clustered_ws_manager.cluster_node.start()
        
        logger.info(f"Clustering setup complete for node {NODE_ID}")
        
    except Exception as e:
        logger.error(f"Failed to setup clustering: {e}")
        logger.warning("Running in single-node mode")
        clustered_ws_manager = None


async def cleanup_clustering():
    """Cleanup clustering infrastructure."""
    if clustered_ws_manager:
        await clustered_ws_manager.cluster_node.stop()
        logger.info(f"Clustering cleanup complete for node {NODE_ID}")


# WebSocket handlers
async def handle_auth(websocket, message):
    """Handle authentication messages."""
    try:
        auth_data = message.get("data", {})
        result = await jwt_authenticator.authenticate(websocket, auth_data)
        
        if result.status == AuthStatus.AUTHENTICATED:
            # Add to authenticated connections
            ws_auth_middleware._authenticated_connections[websocket.connection_id] = result
            
            await websocket.send_json({
                "type": "auth_success",
                "data": {
                    "user_id": result.user_id,
                    "user_data": result.user_data,
                    "node_id": NODE_ID,
                    "expires_at": result.expires_at.isoformat() if result.expires_at else None,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Send cluster info
            if clustered_ws_manager:
                cluster_info = clustered_ws_manager.get_cluster_info()
                await websocket.send_json({
                    "type": "cluster_info",
                    "data": cluster_info
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


async def handle_chat_message(websocket, message):
    """Handle chat messages with clustering."""
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
            "node_id": NODE_ID,
            "timestamp": datetime.now().isoformat()
        },
        sender_id=websocket.connection_id,
        room=room
    )
    
    # Broadcast via cluster if available
    if clustered_ws_manager:
        await clustered_ws_manager.broadcast(chat_message.to_dict(), room)
    else:
        await local_ws_manager.broadcast(chat_message, room)
    
    # Send confirmation
    await websocket.send_json({
        "type": "message_sent",
        "data": {
            "message_id": chat_message.message_id,
            "node_id": NODE_ID,
            "timestamp": chat_message.timestamp.isoformat()
        }
    })


async def handle_private_message(websocket, message):
    """Handle private messages with clustering."""
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
                "node_id": NODE_ID,
                "timestamp": datetime.now().isoformat()
            },
            sender_id=websocket.connection_id
        )
        
        # Send via cluster if available
        if clustered_ws_manager:
            await clustered_ws_manager.send_to_connection(target_id, private_message.to_dict())
        else:
            await local_ws_manager.send_to_connection(target_id, private_message)
        
        # Send confirmation to sender
        await websocket.send_json({
            "type": "private_message_sent",
            "data": {
                "target_id": target_id,
                "message_id": private_message.message_id,
                "node_id": NODE_ID,
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


async def handle_join_room(websocket, message):
    """Handle room join requests."""
    data = message.get("data", {})
    room = data.get("room", "general")
    
    # Join room locally
    local_ws_manager.join_room(websocket.connection_id, room)
    
    # Send confirmation
    await websocket.send_json({
        "type": "room_joined",
        "data": {
            "room": room,
            "connection_id": websocket.connection_id,
            "node_id": NODE_ID,
            "timestamp": datetime.now().isoformat()
        }
    })
    
    # Broadcast user joined message
    join_message = WebSocketMessage(
        type="user_joined",
        data={
            "connection_id": websocket.connection_id,
            "room": room,
            "node_id": NODE_ID,
            "timestamp": datetime.now().isoformat()
        },
        room=room
    )
    
    if clustered_ws_manager:
        await clustered_ws_manager.broadcast(join_message.to_dict(), room)
    else:
        await local_ws_manager.broadcast(join_message, room)


async def handle_leave_room(websocket, message):
    """Handle room leave requests."""
    data = message.get("data", {})
    room = data.get("room", "general")
    
    # Leave room locally
    local_ws_manager.leave_room(websocket.connection_id, room)
    
    # Send confirmation
    await websocket.send_json({
        "type": "room_left",
        "data": {
            "room": room,
            "connection_id": websocket.connection_id,
            "node_id": NODE_ID,
            "timestamp": datetime.now().isoformat()
        }
    })
    
    # Broadcast user left message
    leave_message = WebSocketMessage(
        type="user_left",
        data={
            "connection_id": websocket.connection_id,
            "room": room,
            "node_id": NODE_ID,
            "timestamp": datetime.now().isoformat()
        },
        room=room
    )
    
    if clustered_ws_manager:
        await clustered_ws_manager.broadcast(leave_message.to_dict(), room)
    else:
        await local_ws_manager.broadcast(leave_message, room)


async def handle_get_connections(websocket, message):
    """Handle connection info requests."""
    local_info = local_ws_manager.get_connection_info()
    
    response_data = {
        "local": local_info,
        "node_id": NODE_ID,
        "timestamp": datetime.now().isoformat()
    }
    
    if clustered_ws_manager:
        cluster_info = clustered_ws_manager.get_cluster_info()
        response_data["cluster"] = cluster_info
    
    await websocket.send_json({
        "type": "connections_info",
        "data": response_data
    })


async def handle_ping(websocket, message):
    """Handle ping messages."""
    echo = message.get("data", {}).get("echo", "pong")
    
    await websocket.send_json({
        "type": "pong",
        "data": {
            "echo": echo,
            "node_id": NODE_ID,
            "timestamp": datetime.now().isoformat()
        }
    })


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint with clustering support."""
    try:
        # Accept connection
        await websocket.accept()
        
        # Add to local manager
        await local_ws_manager.add_connection(websocket)
        
        # Add to cluster if available
        if clustered_ws_manager:
            await clustered_ws_manager.add_connection(websocket.connection_id)
        
        # Track connection
        active_connections[websocket.connection_id] = websocket
        
        # Send welcome message
        await websocket.send_json({
            "type": "welcome",
            "data": {
                "message": f"Welcome to Clustered WebSocket Chat! Connected to node {NODE_ID}",
                "connection_id": websocket.connection_id,
                "node_id": NODE_ID,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Send authentication required message
        await websocket.send_json({
            "type": "auth_required",
            "data": {
                "message": "Authentication required. Send auth message with token.",
                "node_id": NODE_ID,
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
                # Handle protected messages
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
        # Remove from tracking
        active_connections.pop(websocket.connection_id, None)
        
        # Remove from local manager
        await local_ws_manager.remove_connection(websocket)
        
        # Remove from cluster if available
        if clustered_ws_manager:
            await clustered_ws_manager.remove_connection(websocket.connection_id)


# HTTP routes
@app.get("/")
async def index(request):
    """Main page with WebSocket client."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Clustered WebSocket Chat - Node {NODE_ID}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .chat-area {{ height: 400px; border: 1px solid #ccc; overflow-y: scroll; padding: 10px; margin: 10px 0; }}
            .input-area {{ display: flex; gap: 10px; margin: 10px 0; }}
            .input-area input, .input-area button {{ padding: 8px; }}
            .input-area input {{ flex: 1; }}
            .status {{ padding: 10px; background: #f0f0f0; margin: 10px 0; }}
            .message {{ margin: 5px 0; padding: 5px; border-radius: 5px; }}
            .message.sent {{ background: #e3f2fd; }}
            .message.received {{ background: #f3e5f5; }}
            .message.system {{ background: #fff3e0; }}
            .rooms {{ display: flex; gap: 10px; margin: 10px 0; }}
            .room {{ padding: 5px 10px; background: #ddd; border-radius: 5px; cursor: pointer; }}
            .room.active {{ background: #4caf50; color: white; }}
            .node-info {{ background: #e8f5e8; padding: 10px; border-radius: 5px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Clustered WebSocket Chat</h1>
            <div class="node-info">
                <strong>Node:</strong> {NODE_ID} | <strong>Port:</strong> {PORT}
            </div>
            
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
            let nodeId = '';

            function connect() {{
                ws = new WebSocket(`ws://localhost:${{PORT}}/ws`);
                
                ws.onopen = function() {{
                    document.getElementById('status').textContent = 'Connected';
                    document.getElementById('status').style.background = '#c8e6c9';
                }};
                
                ws.onmessage = function(event) {{
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                }};
                
                ws.onclose = function() {{
                    document.getElementById('status').textContent = 'Disconnected - Reconnecting...';
                    document.getElementById('status').style.background = '#ffcdd2';
                    setTimeout(connect, 1000);
                }};
                
                ws.onerror = function(error) {{
                    console.error('WebSocket error:', error);
                }};
            }}

            function handleMessage(data) {{
                const chatArea = document.getElementById('chatArea');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message';
                
                switch(data.type) {{
                    case 'welcome':
                        connectionId = data.data.connection_id;
                        nodeId = data.data.node_id;
                        messageDiv.className += ' system';
                        messageDiv.textContent = `Welcome! Your ID: ${{connectionId}} (Node: ${{nodeId}})`; 
                        break;
                        
                    case 'chat':
                        messageDiv.className += data.data.sender_id === connectionId ? ' sent' : ' received';
                        const nodeInfo = data.data.node_id ? ` [Node: ${{data.data.node_id}}]` : '';
                        messageDiv.textContent = `${{data.data.sender_name}}${{nodeInfo}}: ${{data.data.message}}`;
                        break;
                        
                    case 'user_joined':
                        messageDiv.className += ' system';
                        const joinNodeInfo = data.data.node_id ? ` (Node: ${{data.data.node_id}})` : '';
                        messageDiv.textContent = `User joined room: ${{data.data.connection_id}}${{joinNodeInfo}}`;
                        break;
                        
                    case 'user_left':
                        messageDiv.className += ' system';
                        const leaveNodeInfo = data.data.node_id ? ` (Node: ${{data.data.node_id}})` : '';
                        messageDiv.textContent = `User left: ${{data.data.connection_id}}${{leaveNodeInfo}}`;
                        break;
                        
                    case 'private_message':
                        messageDiv.className += ' received';
                        const privateNodeInfo = data.data.node_id ? ` [Node: ${{data.data.node_id}}]` : '';
                        messageDiv.textContent = `[PRIVATE]${{privateNodeInfo}} ${{data.data.sender_name}}: ${{data.data.message}}`;
                        break;
                        
                    case 'pong':
                        messageDiv.className += ' system';
                        const pongNodeInfo = data.data.node_id ? ` (Node: ${{data.data.node_id}})` : '';
                        messageDiv.textContent = `Pong received${{pongNodeInfo}}: ${{data.data.echo}}`;
                        break;
                        
                    case 'cluster_info':
                        messageDiv.className += ' system';
                        messageDiv.textContent = `Cluster info: ${{JSON.stringify(data.data)}}`;
                        break;
                        
                    default:
                        messageDiv.textContent = JSON.stringify(data);
                }}
                
                chatArea.appendChild(messageDiv);
                chatArea.scrollTop = chatArea.scrollHeight;
            }}

            function sendMessage() {{
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                
                if (message && ws && ws.readyState === WebSocket.OPEN) {{
                    ws.send(JSON.stringify({{
                        type: 'chat',
                        data: {{
                            message: message,
                            room: currentRoom,
                            sender_name: username || `User-${{connectionId?.slice(0, 8)}}`
                        }}
                    }}));
                    input.value = '';
                }}
            }}

            function sendPrivateMessage() {{
                const input = document.getElementById('privateInput');
                const text = input.value.trim();
                
                if (text && ws && ws.readyState === WebSocket.OPEN) {{
                    const parts = text.split(':');
                    if (parts.length >= 2) {{
                        const targetId = parts[0].trim();
                        const message = parts.slice(1).join(':').trim();
                        
                        ws.send(JSON.stringify({{
                            type: 'private_message',
                            data: {{
                                target_id: targetId,
                                message: message,
                                sender_name: username || `User-${{connectionId?.slice(0, 8)}}`
                            }}
                        }}));
                        input.value = '';
                    }}
                }}
            }}

            function sendPing() {{
                if (ws && ws.readyState === WebSocket.OPEN) {{
                    ws.send(JSON.stringify({{
                        type: 'ping',
                        data: {{
                            echo: 'Hello from client!'
                        }}
                    }}));
                }}
            }}

            function setUsername() {{
                const input = document.getElementById('usernameInput');
                username = input.value.trim();
                if (username) {{
                    input.value = '';
                    document.getElementById('status').textContent = `Connected as: ${{username}}`;
                }}
            }}

            // Room switching
            document.querySelectorAll('.room').forEach(room => {{
                room.addEventListener('click', function() {{
                    const roomName = this.dataset.room;
                    
                    // Leave current room
                    if (currentRoom && ws && ws.readyState === WebSocket.OPEN) {{
                        ws.send(JSON.stringify({{
                            type: 'leave_room',
                            data: {{ room: currentRoom }}
                        }}));
                    }}
                    
                    // Join new room
                    currentRoom = roomName;
                    if (ws && ws.readyState === WebSocket.OPEN) {{
                        ws.send(JSON.stringify({{
                            type: 'join_room',
                            data: {{ room: roomName }}
                        }}));
                    }}
                    
                    // Update UI
                    document.querySelectorAll('.room').forEach(r => r.classList.remove('active'));
                    this.classList.add('active');
                }});
            }});

            // Enter key handlers
            document.getElementById('messageInput').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') sendMessage();
            }});

            document.getElementById('privateInput').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') sendPrivateMessage();
            }});

            document.getElementById('usernameInput').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') setUsername();
            }});

            // Connect on page load
            connect();
        </script>
    </body>
    </html>
    """
    return Response.html(html)


@app.get("/api/generate-token")
async def generate_token(request):
    """Generate a test JWT token."""
    user_data = {"user_id": "demo_user", "name": "Demo User"}
    token = await jwt_authenticator.create_token(user_data)
    return {"token": token}


@app.get("/api/cluster-info")
async def get_cluster_info(request):
    """Get cluster information."""
    info = {
        "node_id": NODE_ID,
        "port": PORT,
        "local_connections": len(active_connections),
        "timestamp": datetime.now().isoformat()
    }
    
    if clustered_ws_manager:
        cluster_info = clustered_ws_manager.get_cluster_info()
        info["cluster"] = cluster_info
    
    return Response.json(info)


@app.get("/api/broadcast")
async def broadcast_message(request, message: str = "Hello from cluster!"):
    """Broadcast a message to all connected clients across cluster."""
    try:
        broadcast_msg = WebSocketMessage(
            type="broadcast",
            data={
                "message": message,
                "node_id": NODE_ID,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        if clustered_ws_manager:
            await clustered_ws_manager.broadcast(broadcast_msg.to_dict())
        else:
            await local_ws_manager.broadcast(broadcast_msg)
        
        return Response.json({
            "message": "Broadcast sent",
            "node_id": NODE_ID,
            "recipients": len(active_connections)
        })
    except Exception as e:
        return Response.json({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="WebSocket Clustered Application")
    parser.add_argument("--port", type=int, default=PORT, help="Port to run on")
    parser.add_argument("--node-id", type=str, default=NODE_ID, help="Node ID")
    parser.add_argument("--redis-url", type=str, default=REDIS_URL, help="Redis URL")
    
    args = parser.parse_args()
    
    # Update configuration
    NODE_ID = args.node_id
    PORT = args.port
    REDIS_URL = args.redis_url
    
    print(f"🚀 Starting Clustered WebSocket Example...")
    print(f"📖 Node ID: {NODE_ID}")
    print(f"🌐 Port: {PORT}")
    print(f"🔗 Redis URL: {REDIS_URL}")
    print(f"📖 Available endpoints:")
    print(f"  - / - WebSocket chat interface")
    print(f"  - /ws - WebSocket endpoint")
    print(f"  - /api/generate-token - Generate a test token")
    print(f"  - /api/cluster-info - Cluster information")
    print(f"  - /api/broadcast - Broadcast message")
    print(f"  - /docs - API documentation")
    
    # Setup clustering
    asyncio.run(setup_clustering())
    
    try:
        uvicorn.run(app, host="127.0.0.1", port=PORT)
    finally:
        # Cleanup clustering
        asyncio.run(cleanup_clustering()) 