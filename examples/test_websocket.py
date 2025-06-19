import asyncio
import json
import logging
import websockets

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_echo():
    """Test echo WebSocket endpoint"""
    print("Testing Echo WebSocket...")
    async with websockets.connect("ws://localhost:8006/ws/echo") as websocket:
        # Receive welcome message
        welcome = await websocket.recv()
        print(f"Welcome message: {welcome}")
        
        # Send test message
        message = "Hello WebSocket!"
        logger.debug(f"Sending message to echo: {message}")
        await websocket.send(message)
        
        # Receive echo response
        response = await websocket.recv()
        print(f"Echo response: {response}")

async def test_chat():
    """Test chat WebSocket endpoint"""
    print("\nTesting Chat WebSocket...")
    async with websockets.connect("ws://localhost:8006/ws/chat/test-room") as websocket:
        # Receive welcome message
        welcome = await websocket.recv()
        print(f"Welcome message: {welcome}")

        # Send test message
        message = {
            "message": "Hello Chat!",
            "type": "message"
        }
        logger.debug(f"Sending message to chat: {message}")
        await websocket.send(json.dumps(message))

        try:
            # Receive confirmation
        response = await websocket.recv()
            print(f"Chat response: {response}")
        except websockets.exceptions.ConnectionClosed:
            logger.error("Connection closed before receiving response")

async def main():
    try:
    await test_echo()
        await asyncio.sleep(1)  # Wait for echo connection to close
    await test_chat()
    except Exception as e:
        logger.error(f"Test error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
