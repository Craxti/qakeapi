import asyncio
import json
import logging
import websockets
from datetime import datetime
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class WebSocketTestClient:
    """Helper class for WebSocket testing."""
    def __init__(self, uri: str):
        self.uri = uri
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
    
    async def __aenter__(self):
        self.websocket = await websockets.connect(self.uri)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.websocket:
            await self.websocket.close()
    
    async def send_and_receive(self, message: dict) -> dict:
        """Send a message and wait for response."""
        await self.websocket.send(json.dumps(message))
        return json.loads(await self.websocket.recv())

async def test_echo():
    """Test echo WebSocket endpoint."""
    print("\nTesting Echo WebSocket...")
    try:
        async with WebSocketTestClient("ws://localhost:8006/ws/echo") as client:
            # Test normal message
            message = "Hello WebSocket!"
            logger.debug(f"Sending message: {message}")
            await client.websocket.send(message)
            response = await client.websocket.recv()
            print(f"Echo response: {response}")
            assert response == message
            
            # Test long message
            long_message = "x" * 1500
            logger.debug("Sending long message...")
            await client.websocket.send(long_message)
            response = await client.websocket.recv()
            print(f"Long message response: {response}")
            assert response == "Error: Message too long"
            
    except Exception as e:
        logger.error(f"Echo test error: {e}")
        raise

async def test_chat():
    """Test chat WebSocket endpoint with multiple clients."""
    print("\nTesting Chat WebSocket...")
    try:
        # Test room validation
        async with websockets.connect("ws://localhost:8006/ws/chat/!@#") as invalid_ws:
            try:
                await invalid_ws.recv()
                assert False, "Should have rejected invalid room ID"
            except websockets.exceptions.ConnectionClosed as e:
                assert e.code == 4000
                print("✓ Invalid room ID correctly rejected")
        
        # Test normal chat functionality
        room_id = "test-room-1"
        async with WebSocketTestClient(f"ws://localhost:8006/ws/chat/{room_id}") as client1, \
                  WebSocketTestClient(f"ws://localhost:8006/ws/chat/{room_id}") as client2:
            
            # Get welcome messages
            welcome1 = json.loads(await client1.websocket.recv())
            welcome2 = json.loads(await client2.websocket.recv())
            print(f"Welcome messages received: {welcome1['content']}, {welcome2['content']}")
            
            # Test message broadcasting
            test_message = {
                "type": "message",
                "content": "Hello from client 1!",
                "sender": "test_user_1"
            }
            
            # Send from client1
            await client1.send_and_receive(test_message)
            
            # Client2 should receive the message
            response = json.loads(await client2.websocket.recv())
            print(f"Client 2 received: {response}")
            assert response["content"] == test_message["content"]
            assert "timestamp" in response
            
            # Test invalid message format
            invalid_message = {"type": "message"}  # Missing required fields
            await client1.websocket.send(json.dumps(invalid_message))
            error_response = json.loads(await client1.websocket.recv())
            assert error_response["type"] == "error"
            print("✓ Invalid message format correctly handled")
            
    except Exception as e:
        logger.error(f"Chat test error: {e}")
        raise

async def main():
    """Run all WebSocket tests."""
    try:
        await test_echo()
        await asyncio.sleep(1)  # Wait between tests
        await test_chat()
        print("\n✓ All WebSocket tests completed successfully!")
    except Exception as e:
        logger.error(f"Test suite error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
