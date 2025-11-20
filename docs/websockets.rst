WebSocket Guide
==============

QakeAPI provides comprehensive WebSocket support with authentication, clustering, and real-time communication capabilities.

.. contents:: Table of Contents
   :local:

Basic WebSocket Setup
--------------------

Simple WebSocket echo server:

.. code-block:: python

   from qakeapi import Application
   from qakeapi.core.websockets import WebSocketHandler

   app = Application()
   ws_handler = WebSocketHandler()

   @ws_handler.on_connect
   async def handle_connect(websocket):
       await websocket.send_json({"type": "welcome", "message": "Connected!"})

   @ws_handler.on_message
   async def handle_message(websocket, message):
       await websocket.send_json({"type": "echo", "data": message})

   @app.websocket("/ws")
   async def websocket_endpoint(websocket):
       await ws_handler.handle_connection(websocket)

WebSocket with Authentication
----------------------------

Using JWT authentication for WebSocket connections:

.. code-block:: python

   from qakeapi import Application
   from qakeapi.core.websockets import WebSocketHandler
   from qakeapi.security.websocket_auth import WebSocketAuthMiddleware, JWTAuthenticator

   app = Application()
   ws_handler = WebSocketHandler()

   # Setup authentication
   auth_config = AuthConfig(
       secret_key="your-secret-key",
       token_expiry=timedelta(hours=1)
   )
   authenticator = JWTAuthenticator(auth_config)
   auth_middleware = WebSocketAuthMiddleware(authenticator)

   @ws_handler.on_connect
   async def handle_connect(websocket):
       if websocket.authenticated:
           await websocket.send_json({
               "type": "welcome", 
               "message": f"Welcome, {websocket.user_id}!"
           })
       else:
           await websocket.send_json({
               "type": "auth_required", 
               "message": "Please authenticate"
           })

   @ws_handler.on_message
   async def handle_message(websocket, message):
       if not websocket.authenticated:
           await websocket.send_json({
               "type": "error", 
               "message": "Authentication required"
           })
           return

       await websocket.send_json({
           "type": "message", 
           "data": message,
           "user": websocket.user_id
       })

   @app.websocket("/ws")
   async def websocket_endpoint(websocket):
       await auth_middleware(websocket, ws_handler.handle_connection)

   # Token generation endpoint
   @app.post("/api/generate-token")
   async def generate_token(request):
       data = await request.json()
       user_id = data.get("user_id")
       
       token = authenticator.create_token(user_id)
       return {"token": token}

Real-time Chat Application
-------------------------

Complete chat application with rooms and broadcasting:

.. code-block:: python

   from qakeapi import Application
   from qakeapi.core.websockets import WebSocketHandler
   from typing import Dict, Set
   import json

   app = Application()
   ws_handler = WebSocketHandler()

   # Store active connections and rooms
   connections: Dict[str, WebSocket] = {}
   rooms: Dict[str, Set[str]] = defaultdict(set)

   @ws_handler.on_connect
   async def handle_connect(websocket):
       connection_id = str(id(websocket))
       connections[connection_id] = websocket
       
       await websocket.send_json({
           "type": "welcome",
           "connection_id": connection_id,
           "message": "Welcome to the chat!"
       })

   @ws_handler.on_disconnect
   async def handle_disconnect(websocket):
       connection_id = str(id(websocket))
       
       # Remove from connections
       connections.pop(connection_id, None)
       
       # Remove from all rooms
       for room_name, room_connections in rooms.items():
           room_connections.discard(connection_id)
           
           # Notify room members
           await broadcast_to_room(room_name, {
               "type": "user_left",
               "connection_id": connection_id
           })

   @ws_handler.on_message
   async def handle_message(websocket, message):
       try:
           data = json.loads(message) if isinstance(message, str) else message
           msg_type = data.get("type")
           
           if msg_type == "join_room":
               await handle_join_room(websocket, data)
           elif msg_type == "leave_room":
               await handle_leave_room(websocket, data)
           elif msg_type == "chat_message":
               await handle_chat_message(websocket, data)
           else:
               await websocket.send_json({
                   "type": "error",
                   "message": "Unknown message type"
               })
       except Exception as e:
           await websocket.send_json({
               "type": "error",
               "message": f"Error processing message: {str(e)}"
           })

   async def handle_join_room(websocket, data):
       room_name = data.get("room")
       connection_id = str(id(websocket))
       
       if room_name:
           rooms[room_name].add(connection_id)
           
           await websocket.send_json({
               "type": "room_joined",
               "room": room_name
           })
           
           await broadcast_to_room(room_name, {
               "type": "user_joined",
               "connection_id": connection_id,
               "room": room_name
           })

   async def handle_leave_room(websocket, data):
       room_name = data.get("room")
       connection_id = str(id(websocket))
       
       if room_name and room_name in rooms:
           rooms[room_name].discard(connection_id)
           
           await websocket.send_json({
               "type": "room_left",
               "room": room_name
           })
           
           await broadcast_to_room(room_name, {
               "type": "user_left",
               "connection_id": connection_id,
               "room": room_name
           })

   async def handle_chat_message(websocket, data):
       room_name = data.get("room")
       message = data.get("message")
       connection_id = str(id(websocket))
       
       if room_name and message and room_name in rooms:
           await broadcast_to_room(room_name, {
               "type": "chat_message",
               "connection_id": connection_id,
               "room": room_name,
               "message": message
           })

   async def broadcast_to_room(room_name: str, message: dict):
       if room_name in rooms:
           for connection_id in rooms[room_name]:
               if connection_id in connections:
                   try:
                       await connections[connection_id].send_json(message)
                   except:
                       # Remove dead connections
                       connections.pop(connection_id, None)
                       rooms[room_name].discard(connection_id)

   @app.websocket("/ws")
   async def websocket_endpoint(websocket):
       await ws_handler.handle_connection(websocket)

WebSocket Clustering
-------------------

For high-availability applications, use WebSocket clustering with Redis:

.. code-block:: python

   from qakeapi import Application
   from qakeapi.core.clustering import create_clustered_manager
   from qakeapi.core.websockets import WebSocketHandler

   app = Application()
   ws_handler = WebSocketHandler()

   # Create clustered manager
   clustered_manager = create_clustered_manager(
       ws_handler,
       redis_url="redis://localhost:6379",
       node_id="node-1"
   )

   @ws_handler.on_connect
   async def handle_connect(websocket):
       await websocket.send_json({"type": "welcome"})

   @ws_handler.on_message
   async def handle_message(websocket, message):
       # Broadcast to all nodes in cluster
       await clustered_manager.broadcast({
           "type": "message",
           "data": message,
           "node": "node-1"
       })

   @app.websocket("/ws")
   async def websocket_endpoint(websocket):
       await clustered_manager.handle_connection(websocket)

Testing WebSocket Applications
-----------------------------

Testing WebSocket connections and messages:

.. code-block:: python

   import pytest
   import asyncio
   from qakeapi.testing import TestClient
   from examples_app.websocket_app import app

   @pytest.mark.asyncio
   async def test_websocket_connection():
       client = TestClient(app)
       
       # Connect to WebSocket
       async with client.websocket_connect("/ws") as websocket:
           # Should receive welcome message
           welcome = await websocket.receive_json()
           assert welcome["type"] == "welcome"
           
           # Send message
           await websocket.send_json({"type": "message", "text": "Hello"})
           
           # Receive echo
           response = await websocket.receive_json()
           assert response["type"] == "echo"
           assert response["data"]["text"] == "Hello"

   @pytest.mark.asyncio
   async def test_websocket_authentication():
       client = TestClient(app)
       
       # Get auth token
       response = await client.post("/api/generate-token", json={"user_id": "123"})
       token = response.json()["token"]
       
       # Connect with token
       async with client.websocket_connect(f"/ws?token={token}") as websocket:
           # Should receive welcome message
           welcome = await websocket.receive_json()
           assert welcome["type"] == "welcome"
           
           # Send authenticated message
           await websocket.send_json({"type": "message", "text": "Hello"})
           
           # Receive response
           response = await websocket.receive_json()
           assert response["type"] == "message"
           assert response["data"]["text"] == "Hello"

   @pytest.mark.asyncio
   async def test_websocket_chat_room():
       client = TestClient(app)
       
       # Connect first user
       async with client.websocket_connect("/ws") as ws1:
           # Join room
           await ws1.send_json({"type": "join_room", "room": "general"})
           response = await ws1.receive_json()
           assert response["type"] == "room_joined"
           
           # Connect second user
           async with client.websocket_connect("/ws") as ws2:
               # Join same room
               await ws2.send_json({"type": "join_room", "room": "general"})
               response = await ws2.receive_json()
               assert response["type"] == "room_joined"
               
               # Send message from first user
               await ws1.send_json({
                   "type": "chat_message",
                   "room": "general",
                   "message": "Hello everyone!"
               })
               
               # Second user should receive the message
               response = await ws2.receive_json()
               assert response["type"] == "chat_message"
               assert response["message"] == "Hello everyone!"

   @pytest.mark.asyncio
   async def test_websocket_error_handling():
       client = TestClient(app)
       
       async with client.websocket_connect("/ws") as websocket:
           # Send invalid message
           await websocket.send_json({"type": "invalid_type"})
           
           # Should receive error
           response = await websocket.receive_json()
           assert response["type"] == "error"
           assert "Unknown message type" in response["message"]

Performance Testing
------------------

Load testing WebSocket connections:

.. code-block:: python

   import asyncio
   import time
   from qakeapi.testing import TestClient

   async def test_websocket_performance():
       client = TestClient(app)
       connections = []
       messages_sent = 0
       messages_received = 0
       
       # Create multiple connections
       for i in range(100):
           websocket = await client.websocket_connect("/ws")
           connections.append(websocket)
       
       start_time = time.time()
       
       # Send messages from all connections
       for i, websocket in enumerate(connections):
           await websocket.send_json({
               "type": "message",
               "text": f"Message {i}"
           })
           messages_sent += 1
       
       # Receive responses
       for websocket in connections:
           response = await websocket.receive_json()
           messages_received += 1
       
       end_time = time.time()
       duration = end_time - start_time
       
       print(f"Sent {messages_sent} messages in {duration:.2f}s")
       print(f"Rate: {messages_sent/duration:.2f} messages/second")
       
       # Close connections
       for websocket in connections:
           await websocket.close()

WebSocket Client Example
-----------------------

JavaScript client for the chat application:

.. code-block:: html

   <!DOCTYPE html>
   <html>
   <head>
       <title>WebSocket Chat</title>
   </head>
   <body>
       <div id="chat">
           <div id="messages"></div>
           <input type="text" id="message" placeholder="Type a message...">
           <button onclick="sendMessage()">Send</button>
       </div>
       
       <script>
           const ws = new WebSocket('ws://localhost:8000/ws');
           const messagesDiv = document.getElementById('messages');
           const messageInput = document.getElementById('message');
           
           ws.onopen = function() {
               console.log('Connected to WebSocket');
           };
           
           ws.onmessage = function(event) {
               const data = JSON.parse(event.data);
               
               switch(data.type) {
                   case 'welcome':
                       addMessage(`System: ${data.message}`);
                       break;
                   case 'chat_message':
                       addMessage(`${data.connection_id}: ${data.message}`);
                       break;
                   case 'user_joined':
                       addMessage(`System: User ${data.connection_id} joined`);
                       break;
                   case 'user_left':
                       addMessage(`System: User ${data.connection_id} left`);
                       break;
                   case 'error':
                       addMessage(`Error: ${data.message}`);
                       break;
               }
           };
           
           ws.onclose = function() {
               addMessage('System: Disconnected from server');
           };
           
           function sendMessage() {
               const message = messageInput.value;
               if (message.trim()) {
                   ws.send(JSON.stringify({
                       type: 'chat_message',
                       room: 'general',
                       message: message
                   }));
                   messageInput.value = '';
               }
           }
           
           function addMessage(text) {
               const div = document.createElement('div');
               div.textContent = text;
               messagesDiv.appendChild(div);
               messagesDiv.scrollTop = messagesDiv.scrollHeight;
           }
           
           // Send message on Enter key
           messageInput.addEventListener('keypress', function(e) {
               if (e.key === 'Enter') {
                   sendMessage();
               }
           });
       </script>
   </body>
   </html>

Best Practices
--------------

1. **Error Handling**: Always handle WebSocket errors and disconnections
2. **Authentication**: Use JWT tokens for secure WebSocket connections
3. **Rate Limiting**: Implement rate limiting for WebSocket messages
4. **Connection Management**: Track and clean up dead connections
5. **Testing**: Test WebSocket functionality thoroughly
6. **Monitoring**: Monitor WebSocket performance and connection counts
7. **Clustering**: Use clustering for high-availability applications

Common Patterns
---------------

Connection Pooling
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class ConnectionPool:
       def __init__(self, max_connections=1000):
           self.connections = {}
           self.max_connections = max_connections
       
       async def add_connection(self, connection_id: str, websocket):
           if len(self.connections) >= self.max_connections:
               # Remove oldest connection
               oldest_id = next(iter(self.connections))
               await self.remove_connection(oldest_id)
           
           self.connections[connection_id] = websocket
       
       async def remove_connection(self, connection_id: str):
           if connection_id in self.connections:
               websocket = self.connections[connection_id]
               await websocket.close()
               del self.connections[connection_id]
       
       async def broadcast(self, message: dict):
           dead_connections = []
           
           for connection_id, websocket in self.connections.items():
               try:
                   await websocket.send_json(message)
               except:
                   dead_connections.append(connection_id)
           
           # Clean up dead connections
           for connection_id in dead_connections:
               await self.remove_connection(connection_id)

Message Queuing
~~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   from collections import defaultdict

   class MessageQueue:
       def __init__(self):
           self.queues = defaultdict(asyncio.Queue)
       
       async def enqueue(self, room: str, message: dict):
           await self.queues[room].put(message)
       
       async def dequeue(self, room: str):
           return await self.queues[room].get()
       
       async def broadcast_worker(self, room: str, connections: set):
           while True:
               try:
                   message = await self.dequeue(room)
                   
                   dead_connections = set()
                   for websocket in connections:
                       try:
                           await websocket.send_json(message)
                       except:
                           dead_connections.add(websocket)
                   
                   # Remove dead connections
                   connections -= dead_connections
                   
               except asyncio.CancelledError:
                   break 