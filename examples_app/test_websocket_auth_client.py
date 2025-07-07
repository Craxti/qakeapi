#!/usr/bin/env python3
"""
WebSocket Authentication Test Client

Тестирует WebSocket аутентификацию с JWT токенами.
"""

import asyncio
import json
import aiohttp
import websockets
from datetime import datetime

async def get_auth_token():
    """Получить JWT токен для аутентификации."""
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8021/api/generate-token') as response:
            data = await response.json()
            return data['token']

async def test_websocket_with_auth():
    """Тест WebSocket с аутентификацией."""
    print("🔐 Тестирование WebSocket с аутентификацией...")
    
    # Получаем токен
    token = await get_auth_token()
    print(f"✅ Получен токен: {token[:50]}...")
    
    # Подключаемся к WebSocket
    uri = "ws://localhost:8021/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Подключение к WebSocket установлено")
            
            # Получаем welcome сообщение
            welcome_response = await websocket.recv()
            welcome_data = json.loads(welcome_response)
            print(f"📥 Welcome: {welcome_data}")
            
            # Получаем auth_required сообщение
            auth_required_response = await websocket.recv()
            auth_required_data = json.loads(auth_required_response)
            print(f"📥 Auth required: {auth_required_data}")
            
            # Отправляем аутентификацию
            auth_message = {
                "type": "auth",
                "data": {"token": token}
            }
            await websocket.send(json.dumps(auth_message))
            print("📤 Отправлен запрос аутентификации")
            
            # Получаем ответ на аутентификацию
            response = await websocket.recv()
            auth_response = json.loads(response)
            print(f"📥 Ответ аутентификации: {auth_response}")
            
            if auth_response.get('type') == 'auth_success':
                print("✅ Аутентификация успешна!")
                
                # Получаем connection_info
                info_response = await websocket.recv()
                info_data = json.loads(info_response)
                print(f"📥 Connection info: {info_data}")
                
                # Тестируем отправку сообщения в чат
                chat_message = {
                    "type": "chat",
                    "data": {
                        "message": "Привет! Это тестовое сообщение с аутентификацией",
                        "room": "test_room",
                        "sender_name": "TestUser"
                    }
                }
                await websocket.send(json.dumps(chat_message))
                print("📤 Отправлено сообщение в чат")
                
                # Получаем подтверждение
                response = await websocket.recv()
                chat_response = json.loads(response)
                print(f"📥 Ответ чата: {chat_response}")
                
                # Тестируем приватное сообщение
                private_message = {
                    "type": "private_message",
                    "data": {
                        "target_id": "other_user",
                        "message": "Приватное сообщение",
                        "sender_name": "TestUser"
                    }
                }
                await websocket.send(json.dumps(private_message))
                print("📤 Отправлено приватное сообщение")
                
                # Получаем подтверждение
                response = await websocket.recv()
                private_response = json.loads(response)
                print(f"📥 Ответ приватного сообщения: {private_response}")
                
            else:
                print("❌ Аутентификация не удалась")
                
    except Exception as e:
        print(f"❌ Ошибка WebSocket: {e}")

async def test_websocket_without_auth():
    """Тест WebSocket без аутентификации."""
    print("\n🚫 Тестирование WebSocket без аутентификации...")
    
    uri = "ws://localhost:8021/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Подключение к WebSocket установлено")
            
            # Получаем welcome сообщение
            welcome_response = await websocket.recv()
            welcome_data = json.loads(welcome_response)
            print(f"📥 Welcome: {welcome_data}")
            
            # Получаем auth_required сообщение
            auth_required_response = await websocket.recv()
            auth_required_data = json.loads(auth_required_response)
            print(f"📥 Auth required: {auth_required_data}")
            
            # Пытаемся отправить сообщение без аутентификации
            chat_message = {
                "type": "chat",
                "data": {
                    "message": "Сообщение без аутентификации",
                    "room": "test_room"
                }
            }
            await websocket.send(json.dumps(chat_message))
            print("📤 Отправлено сообщение без аутентификации")
            
            # Должны получить ошибку аутентификации
            response = await websocket.recv()
            error_response = json.loads(response)
            print(f"📥 Ответ (ожидается ошибка): {error_response}")
            
            if error_response.get('type') == 'error' and 'AUTH_REQUIRED' in str(error_response):
                print("✅ Правильно получена ошибка аутентификации")
            else:
                print("⚠️ Неожиданный ответ")
                
    except Exception as e:
        print(f"❌ Ошибка WebSocket: {e}")

async def test_invalid_token():
    """Тест с неверным токеном."""
    print("\n🚫 Тестирование с неверным токеном...")
    
    uri = "ws://localhost:8021/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Подключение к WebSocket установлено")
            
            # Получаем welcome сообщение
            welcome_response = await websocket.recv()
            welcome_data = json.loads(welcome_response)
            print(f"📥 Welcome: {welcome_data}")
            
            # Получаем auth_required сообщение
            auth_required_response = await websocket.recv()
            auth_required_data = json.loads(auth_required_response)
            print(f"📥 Auth required: {auth_required_data}")
            
            # Отправляем неверный токен
            auth_message = {
                "type": "auth",
                "data": {"token": "invalid_token_123"}
            }
            await websocket.send(json.dumps(auth_message))
            print("📤 Отправлен неверный токен")
            
            # Получаем ответ на аутентификацию
            response = await websocket.recv()
            auth_response = json.loads(response)
            print(f"📥 Ответ аутентификации: {auth_response}")
            
            if auth_response.get('type') == 'auth_error':
                print("✅ Правильно получена ошибка неверного токена")
            else:
                print("⚠️ Неожиданный ответ")
                
    except Exception as e:
        print(f"❌ Ошибка WebSocket: {e}")

async def main():
    """Основная функция тестирования."""
    print("🚀 Запуск тестов WebSocket аутентификации")
    print("=" * 50)
    
    # Проверяем, что сервер запущен
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8021/') as response:
                if response.status == 200:
                    print("✅ Сервер WebSocket запущен")
                else:
                    print("❌ Сервер не отвечает")
                    return
    except Exception as e:
        print(f"❌ Не удается подключиться к серверу: {e}")
        return
    
    # Запускаем тесты
    await test_websocket_with_auth()
    await test_websocket_without_auth()
    await test_invalid_token()
    
    print("\n" + "=" * 50)
    print("🏁 Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(main()) 