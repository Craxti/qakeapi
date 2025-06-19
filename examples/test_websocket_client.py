import asyncio
import json
import websockets

async def test_echo():
    uri = "ws://localhost:8003/ws/echo"
    async with websockets.connect(uri) as websocket:
        message = "Hello, Echo!"
        await websocket.send(message)
        print(f"Sent to echo: {message}")

        response = await websocket.recv()
        print(f"Received from echo: {response}")

async def test_chat():
    uri = "ws://localhost:8003/ws/chat/test-room"
    async with websockets.connect(uri) as websocket:
        message = json.dumps({
            "message": "Hello, Chat!",
            "sender": "test-client"
        })
        await websocket.send(message)
        print(f"Sent to chat: {message}")
        
        response = await websocket.recv()
        print(f"Received from chat: {response}")

async def main():
    print("Testing Echo WebSocket...")
    await test_echo()

    print("\nTesting Chat WebSocket...")
    await test_chat()

if __name__ == "__main__":
    asyncio.run(main())
