"""
Входной файл для запуска всех примеров QakeAPI.
"""
import multiprocessing
import time
import requests
import json
import websockets
import asyncio
from typing import Dict, Any

# Порты для каждого приложения
PORTS = {
    "basic": 8000,
    "caching": 8001,
    "profiling": 8002,
    "websocket": 8006,
    "jwt_auth": 8008,
    "cors": 8009,
    "rate_limit": 8010,
    "background_tasks": 8011,
    "simple": 8012,
    "auth": 8013,
    "security": 8014
}

def run_app(module_name: str, port: int):
    """Запуск приложения на указанном порту."""
    import uvicorn
    app_module = __import__(module_name, fromlist=['app'])
    uvicorn.run(app_module.app, host="127.0.0.1", port=port)

def test_basic_app():
    """Тестирование эндпоинтов basic_app."""
    base_url = f"http://127.0.0.1:{PORTS['basic']}"
    
    print("\nBasic App Tests:")
    print("-" * 50)
    
    # Тест корневого эндпоинта
    response = requests.get(f"{base_url}/")
    print("\n1. Root endpoint (GET /):")
    print(response.json())
    
    # Создание пользователя
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "StrongPass123!",
        "full_name": "Test User"
    }
    response = requests.post(f"{base_url}/users", json=user_data)
    print("\n2. Create user (POST /users):")
    print(response.json())
    
    # Получение списка пользователей
    response = requests.get(f"{base_url}/users")
    print("\n3. List users (GET /users):")
    print(response.json())
    
    # Получение пользователя
    response = requests.get(f"{base_url}/users/testuser")
    print("\n4. Get user (GET /users/testuser):")
    print(response.json())
    
    # Обновление пользователя
    update_data = {
        "full_name": "Updated Test User"
    }
    response = requests.put(f"{base_url}/users/testuser", json=update_data)
    print("\n5. Update user (PUT /users/testuser):")
    print(response.json())
    
    # Удаление пользователя
    response = requests.delete(f"{base_url}/users/testuser")
    print("\n6. Delete user (DELETE /users/testuser):")
    print(response.json())

def test_caching_app():
    """Тестирование эндпоинтов caching_app."""
    base_url = f"http://127.0.0.1:{PORTS['caching']}"
    
    print("\nCaching App Tests:")
    print("-" * 50)
    
    # Тест вычислений с кэшированием
    print("\n1. Compute with caching (GET /compute/42):")
    start = time.time()
    response = requests.get(f"{base_url}/compute/42")
    print(f"First request (uncached): {time.time() - start:.2f}s")
    print(response.json())
    
    start = time.time()
    response = requests.get(f"{base_url}/compute/42")
    print(f"Second request (cached): {time.time() - start:.2f}s")
    print(response.json())
    
    # Тест вычислений без кэширования
    print("\n2. Compute without caching (GET /compute-nocache/42):")
    start = time.time()
    response = requests.get(f"{base_url}/compute-nocache/42")
    print(f"Request time: {time.time() - start:.2f}s")
    print(response.json())
    
    # Очистка конкретного ключа кэша
    print("\n3. Clear specific cache (DELETE /cache/42):")
    response = requests.delete(f"{base_url}/cache/42")
    print(response.json())
    
    # Очистка всего кэша
    print("\n4. Clear all cache (DELETE /cache):")
    response = requests.delete(f"{base_url}/cache")
    print(response.json())

def test_profiling_app():
    """Тестирование эндпоинтов profiling_app."""
    base_url = f"http://127.0.0.1:{PORTS['profiling']}"
    
    print("\nProfiling App Tests:")
    print("-" * 50)
    
    # Тест быстрого эндпоинта
    print("\n1. Fast endpoint (GET /fast):")
    response = requests.get(f"{base_url}/fast")
    print(response.json())
    
    # Тест медленного эндпоинта
    print("\n2. Slow endpoint (GET /slow):")
    response = requests.get(f"{base_url}/slow")
    print(response.json())
    
    # Тест CPU-интенсивного эндпоинта
    print("\n3. CPU-intensive endpoint (GET /cpu-intensive):")
    response = requests.get(f"{base_url}/cpu-intensive")
    print(response.json())
    
    # Тест Memory-интенсивного эндпоинта
    print("\n4. Memory-intensive endpoint (GET /memory-intensive):")
    response = requests.get(f"{base_url}/memory-intensive")
    print(response.json())
    
    # Получение общей статистики
    print("\n5. Get all stats (GET /stats):")
    response = requests.get(f"{base_url}/stats")
    print(json.dumps(response.json(), indent=2))
    
    # Получение статистики конкретного эндпоинта
    print("\n6. Get endpoint stats (GET /stats/fast_endpoint):")
    response = requests.get(f"{base_url}/stats/fast_endpoint")
    print(json.dumps(response.json(), indent=2))

async def test_websocket_app():
    """Тестирование WebSocket приложения."""
    print("\nWebSocket App Tests:")
    print("-" * 50)
    
    # Тест echo endpoint
    uri = f"ws://127.0.0.1:{PORTS['websocket']}/ws/echo"
    async with websockets.connect(uri) as websocket:
        message = "Hello, WebSocket!"
        await websocket.send(message)
        response = await websocket.recv()
        print("\n1. Echo test:")
        print(f"Sent: {message}")
        print(f"Received: {response}")
    
    # Тест chat endpoint
    uri = f"ws://127.0.0.1:{PORTS['websocket']}/ws/chat/test-room"
    async with websockets.connect(uri) as websocket:
        message = json.dumps({
            "type": "message",
            "content": "Hello, Chat!",
            "sender": "test-user"
        })
        await websocket.send(message)
        response = await websocket.recv()
        print("\n2. Chat test:")
        print(f"Sent: {message}")
        print(f"Received: {response}")

def test_jwt_auth_app():
    """Тестирование JWT Auth приложения."""
    base_url = f"http://127.0.0.1:{PORTS['jwt_auth']}"
    
    print("\nJWT Auth App Tests:")
    print("-" * 50)
    
    # Тест корневого эндпоинта
    response = requests.get(f"{base_url}/")
    print("\n1. Root endpoint:")
    print(response.json())
    
    # Тест логина
    login_data = {"username": "admin", "password": "admin"}
    response = requests.post(f"{base_url}/login", json=login_data)
    print("\n2. Login test:")
    print(response.json())
    token = response.json()["access_token"]
    
    # Тест защищенного эндпоинта
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{base_url}/protected", headers=headers)
    print("\n3. Protected endpoint test:")
    print(response.json())
    
    # Тест админского эндпоинта
    response = requests.get(f"{base_url}/admin", headers=headers)
    print("\n4. Admin endpoint test:")
    print(response.json())

def test_cors_app():
    """Тестирование CORS приложения."""
    base_url = f"http://127.0.0.1:{PORTS['cors']}"
    
    print("\nCORS App Tests:")
    print("-" * 50)
    
    headers = {"Origin": "http://localhost:3000"}
    response = requests.get(f"{base_url}/", headers=headers)
    print("\n1. CORS headers test:")
    print("Access-Control-Allow-Origin:", response.headers.get("Access-Control-Allow-Origin"))
    print("Access-Control-Allow-Methods:", response.headers.get("Access-Control-Allow-Methods"))

def test_rate_limit_app():
    """Тестирование Rate Limit приложения."""
    base_url = f"http://127.0.0.1:{PORTS['rate_limit']}"
    
    print("\nRate Limit App Tests:")
    print("-" * 50)
    
    print("\n1. Rate limit test:")
    for i in range(12):  # Превышаем лимит в 10 запросов
        response = requests.get(f"{base_url}/")
        print(f"Request {i+1}: {response.status_code}")
        if response.status_code == 429:
            print("Rate limit exceeded as expected")
            break

def test_background_tasks_app():
    """Тестирование Background Tasks приложения."""
    base_url = f"http://127.0.0.1:{PORTS['background_tasks']}"
    
    print("\nBackground Tasks App Tests:")
    print("-" * 50)
    
    # Запуск длительной задачи
    response = requests.post(f"{base_url}/tasks", json={"task_type": "long_running"})
    task_id = response.json()["task_id"]
    print("\n1. Task creation:")
    print(response.json())
    
    # Проверка статуса
    time.sleep(2)
    response = requests.get(f"{base_url}/tasks/{task_id}")
    print("\n2. Task status:")
    print(response.json())

def test_simple_app():
    """Тестирование Simple приложения."""
    base_url = f"http://127.0.0.1:{PORTS['simple']}"
    
    print("\nSimple App Tests:")
    print("-" * 50)
    
    response = requests.get(f"{base_url}/")
    print("\n1. Root endpoint:")
    print(response.json())

def test_auth_app():
    """Тестирование Auth приложения."""
    base_url = f"http://127.0.0.1:{PORTS['auth']}"
    
    print("\nAuth App Tests:")
    print("-" * 50)
    
    # Регистрация
    register_data = {
        "username": "testuser",
        "password": "testpass",
        "email": "test@example.com"
    }
    response = requests.post(f"{base_url}/register", json=register_data)
    print("\n1. Registration:")
    print(response.json())
    
    # Логин
    login_data = {
        "username": "testuser",
        "password": "testpass"
    }
    response = requests.post(f"{base_url}/login", json=login_data)
    print("\n2. Login:")
    print(response.json())

def test_security_app():
    """Тестирование Security приложения."""
    base_url = f"http://127.0.0.1:{PORTS['security']}"
    
    print("\nSecurity App Tests:")
    print("-" * 50)
    
    response = requests.get(f"{base_url}/secure")
    print("\n1. Secure endpoint (without token):")
    print(response.json())

def main():
    """Основная функция запуска и тестирования."""
    # Запуск всех приложений в отдельных процессах
    processes = []
    for app_name, port in PORTS.items():
        module_name = f"{app_name}_app"
        if app_name == "background_tasks":
            module_name = "background_tasks_app"
        
        p = multiprocessing.Process(
            target=run_app,
            args=(module_name, port)
        )
        processes.append(p)
        p.start()
    
    print("Waiting for applications to start...")
    time.sleep(5)  # Даем больше времени на запуск всех приложений
    
    try:
        # Тестирование всех приложений
        test_basic_app()
        test_caching_app()
        test_profiling_app()
        asyncio.run(test_websocket_app())
        test_jwt_auth_app()
        test_cors_app()
        test_rate_limit_app()
        test_background_tasks_app()
        test_simple_app()
        test_auth_app()
        test_security_app()
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to one or more applications")
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    finally:
        # Завершение процессов
        for p in processes:
            p.terminate()
            p.join()

if __name__ == "__main__":
    main()
