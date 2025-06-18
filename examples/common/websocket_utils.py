import json
import logging
from typing import Dict, Any, Optional

from qakeapi.core.websockets import WebSocket, WebSocketState

logger = logging.getLogger(__name__)

async def send_error(websocket: WebSocket, message: str) -> None:
    """Отправка сообщения об ошибке"""
    try:
        await websocket.send_json({"type": "error", "message": message})
    except Exception as e:
        logger.error(f"Error sending error message: {e}")

async def handle_websocket_message(
    websocket: WebSocket,
    message: str | bytes | Dict,
    handler: callable,
    error_handler: callable = None
) -> None:
    """Обработка входящего WebSocket сообщения"""
    try:
        if isinstance(message, str):
            data = json.loads(message)
        else:
            data = message

        logger.debug(f"Parsed message data: {data}")
        await handler(data)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        await send_error(websocket, "Invalid JSON format")
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        if error_handler:
            await error_handler(e)
        else:
            await send_error(websocket, str(e))

async def safe_close_websocket(websocket: WebSocket, code: int = 1000) -> None:
    """Безопасное закрытие WebSocket соединения"""
    if websocket.state == WebSocketState.CONNECTED:
        try:
            await websocket.close(code)
            logger.debug("Closed WebSocket connection")
        except Exception as e:
            logger.error(f"Error closing WebSocket: {e}") 