import asyncio
import json
import websockets
from config import PORTS


async def test_chat():
    # Подключаемся к чату в комнате test_room
    async with websockets.connect(f"ws://localhost:{PORTS['websocket_app']}/ws/chat/test_room") as websocket:
        # Получаем приветственное сообщение
        response = await websocket.recv()
        print(f"Received: {response}")

        # Отправляем сообщение
        message = {"type": "message", "message": "Hello from test client!"}
        await websocket.send(json.dumps(message))

        # Получаем ответ
        response = await websocket.recv()
        print(f"Received: {response}")


async def test_echo():
    # Подключаемся к echo endpoint
    async with websockets.connect(f"ws://localhost:{PORTS['websocket_app']}/ws/echo") as websocket:
        # Отправляем сообщение
        message = "Hello, Echo!"
        await websocket.send(message)

        # Получаем ответ
        response = await websocket.recv()
        print(f"Received from echo: {response}")


async def main():
    # Тестируем оба endpoint'а
    await asyncio.gather(test_chat(), test_echo())


if __name__ == "__main__":
    asyncio.run(main())
