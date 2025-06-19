import json
import logging
from typing import Dict, List, Optional

from qakeapi.core.application import Application
from qakeapi.core.websockets import WebSocket
from qakeapi.core.responses import Response, JSONResponse
from qakeapi.core.requests import Request

WEBSOCKET_PORT = 8006  # Используем фиксированный порт

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='websocket.log'
)
logger = logging.getLogger(__name__)

# Create application
app = Application()

# Store active connections per room
connections: Dict[str, List[WebSocket]] = {}

class MessageRequest:
    def __init__(self, type: str, content: str, sender: Optional[str] = None):
        self.type = type
        self.content = content
        self.sender = sender

    @classmethod
    def parse_raw(cls, data: str) -> "MessageRequest":
        try:
            json_data = json.loads(data)
            return cls(
                type=json_data.get("type", "message"),
                content=json_data.get("content", ""),
                sender=json_data.get("sender")
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {str(e)}")
            raise

@app.websocket("/ws/chat/{room_id}")
async def chat(websocket: WebSocket, room_id: str):
    await websocket.accept()
    logger.info(f"New connection in room {room_id}")

    try:
        # Initialize room if not exists
        if room_id not in connections:
            connections[room_id] = []
        connections[room_id].append(websocket)
        
        while True:
            try:
                data = await websocket.receive_text()
                if not data:
                    continue

                message = MessageRequest.parse_raw(data)
                response_data = {
                    "type": message.type,
                    "content": message.content,
                    "sender": message.sender or "anonymous"
                }

                # Broadcast message to all clients in room
                for client in connections[room_id]:
                    try:
                        await client.send_json(response_data)
                    except Exception as e:
                        logger.error(f"Failed to send to client: {str(e)}")
                        connections[room_id].remove(client)

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid message format"
                })
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                break

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Cleanup connection
        if room_id in connections:
            connections[room_id] = [conn for conn in connections[room_id] if conn != websocket]
            if not connections[room_id]:
                del connections[room_id]
        logger.info(f"Connection closed in room {room_id}")

@app.websocket("/ws/echo")
async def echo(websocket: WebSocket):
    await websocket.accept()
    logger.info("New echo connection")

    try:
        while True:
            data = await websocket.receive_text()
            if data:
                await websocket.send_text(data)
    except Exception as e:
        logger.error(f"Echo error: {str(e)}")
    finally:
        logger.info("Echo connection closed")

@app.get("/")
async def index(request: Request) -> Response:
    return JSONResponse(
        content={"message": "WebSocket server is running"},
        status_code=200
    )

if __name__ == "__main__":
    import uvicorn
    print("Starting WebSocket example server...")
    uvicorn.run(app, host="0.0.0.0", port=WEBSOCKET_PORT)
