"""
WebSocket example.

Demonstrates:
- WebSocket connections
- Sending and receiving messages
- JSON message handling
"""

from qakeapi import QakeAPI, WebSocket
import json


app = QakeAPI(title="WebSocket Example")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Simple WebSocket echo server."""
    await websocket.accept()
    
    await websocket.send_json({
        "type": "connection",
        "message": "Connected!",
    })
    
    try:
        async for message in websocket.iter_json():
            # Echo message back
            await websocket.send_json({
                "type": "echo",
                "data": message,
            })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """Chat WebSocket server."""
    await websocket.accept()
    
    await websocket.send_json({
        "type": "system",
        "message": "Welcome to chat!",
    })
    
    try:
        async for message in websocket.iter_json():
            msg_type = message.get("type")
            
            if msg_type == "message":
                # Broadcast message
                await websocket.send_json({
                    "type": "message",
                    "user": message.get("user", "Anonymous"),
                    "text": message.get("text", ""),
                })
            elif msg_type == "ping":
                # Respond to ping
                await websocket.send_json({
                    "type": "pong",
                })
    except Exception as e:
        print(f"Chat error: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

