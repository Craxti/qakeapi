import asyncio
import websockets
import json

async def test_echo():
    uri = "ws://localhost:8000/ws/echo"
    async with websockets.connect(uri) as websocket:
        # Send a message
        await websocket.send("Hello, WebSocket!")
        # Receive the response
        response = await websocket.recv()
        print(f"Received from echo: {response}")

async def test_chat():
    uri = "ws://localhost:8000/ws/chat/test-room"
    async with websockets.connect(uri) as websocket:
        # Receive welcome message
        welcome = await websocket.recv()
        print(f"Welcome message: {welcome}")
        
        # Send a chat message
        message = {
            "type": "chat",
            "message": "Hello, chat room!"
        }
        await websocket.send(json.dumps(message))
        
        # Receive the broadcasted message
        response = await websocket.recv()
        print(f"Received from chat: {response}")

async def main():
    print("Testing echo WebSocket...")
    await test_echo()
    print("\nTesting chat WebSocket...")
    await test_chat()

if __name__ == "__main__":
    asyncio.run(main()) 