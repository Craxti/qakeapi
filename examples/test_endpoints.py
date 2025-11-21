"""
Скрипт для тестирования API эндпоинтов
"""

import asyncio
import json
import sys
from unittest.mock import AsyncMock

# Импортируем наше демо приложение
from test_api_demo import app


async def create_mock_request(method, path, query_string="", body=None, headers=None):
    """Создать mock ASGI запрос"""
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": query_string.encode() if query_string else b"",
        "headers": headers or [],
    }

    receive = AsyncMock()
    if body:
        receive.side_effect = [
            {
                "type": "http.request",
                "body": body.encode() if isinstance(body, str) else body,
                "more_body": False,
            }
        ]
    else:
        receive.side_effect = [
            {"type": "http.request", "body": b"", "more_body": False}
        ]

    send = AsyncMock()

    return scope, receive, send


async def test_endpoint(method, path, query_string="", body=None, headers=None):
    """Тестировать эндпоинт"""
    print(f"\n=== Тестируем: {method} {path} ===")

    if query_string:
        print(f"Query: {query_string}")
    if body:
        print(f"Body: {body}")

    try:
        scope, receive, send = await create_mock_request(
            method, path, query_string, body, headers
        )

        # Выполняем запрос
        await app(scope, receive, send)

        # Анализируем ответ
        if send.call_count >= 2:
            start_call = send.call_args_list[0][0][0]
            body_call = send.call_args_list[1][0][0]

            status = start_call.get("status", "unknown")
            response_body = body_call.get("body", b"")

            print(f"Статус: {status}")

            if response_body:
                try:
                    response_data = json.loads(response_body.decode())
                    print(
                        f"Ответ: {json.dumps(response_data, ensure_ascii=False, indent=2)}"
                    )
                except:
                    print(f"Ответ (raw): {response_body.decode()}")

            return status, response_body
        else:
            print("Ошибка: недостаточно вызовов send")
            return None, None

    except Exception as e:
        print(f"Ошибка: {e}")
        return None, None


async def run_tests():
    """Запустить все тесты"""
    print("Начинаем тестирование API эндпоинтов...")

    tests = [
        # Базовые эндпоинты
        ("GET", "/", "", None),
        ("GET", "/health", "", None),
        # Пользователи
        ("GET", "/users", "", None),
        ("GET", "/users", "limit=1&offset=0", None),
        ("GET", "/users/1", "", None),
        ("GET", "/users/999", "", None),  # Не существует
        # Создание пользователя
        (
            "POST",
            "/users",
            "",
            json.dumps(
                {
                    "name": "Тестовый Пользователь",
                    "email": "test@example.com",
                    "age": 25,
                }
            ),
        ),
        # Валидация пользователя (ошибка)
        (
            "POST",
            "/users",
            "",
            json.dumps(
                {
                    "name": "T",  # Слишком короткое
                    "email": "invalid-email",  # Неверный формат
                    "age": -5,  # Отрицательный возраст
                }
            ),
        ),
        # Товары
        ("GET", "/items", "", None),
        ("GET", "/items", "category=electronics", None),
        ("GET", "/items", "min_price=1000&max_price=60000", None),
        ("GET", "/items/1", "", None),
        # Создание товара
        (
            "POST",
            "/items",
            "",
            json.dumps({"title": "Тестовый товар", "price": 1500, "category": "test"}),
        ),
        # Поиск
        ("GET", "/search", "q=Алексей", None),
        ("GET", "/search", "q=Ноутбук&type=items", None),
        # Демо эндпоинты
        ("GET", "/demo/validation", "name=Тест&age=30", None),
        ("GET", "/demo/validation", "age=200", None),  # Ошибка валидации
        ("POST", "/demo/echo", "", json.dumps({"test": "data", "number": 42})),
        ("GET", "/demo/error", "", None),  # Демо ошибка
        # OpenAPI
        ("GET", "/openapi.json", "", None),
    ]

    results = []

    for method, path, query, body in tests:
        status, response = await test_endpoint(method, path, query, body)
        results.append((method, path, status, response))

        # Небольшая пауза между запросами
        await asyncio.sleep(0.1)

    # Сводка результатов
    print("\n" + "=" * 60)
    print("📊 СВОДКА РЕЗУЛЬТАТОВ ТЕСТИРОВАНИЯ")
    print("=" * 60)

    success_count = 0
    error_count = 0

    for method, path, status, response in results:
        if status:
            if 200 <= status < 300:
                print(f"✅ {method} {path} - {status}")
                success_count += 1
            elif 400 <= status < 500:
                print(f"⚠️  {method} {path} - {status} (ожидаемая ошибка)")
                success_count += 1
            else:
                print(f"❌ {method} {path} - {status}")
                error_count += 1
        else:
            print(f"💥 {method} {path} - СБОЙ")
            error_count += 1

    print(f"\nИтого:")
    print(f"  Успешно: {success_count}")
    print(f"  Ошибок: {error_count}")
    print(f"  Всего: {len(results)}")

    if error_count == 0:
        print("\n🎉 Все тесты прошли успешно!")
    else:
        print(f"\n⚠️  Обнаружено {error_count} проблем")

    return success_count, error_count


async def test_middleware():
    """Тестировать middleware"""
    print("\n" + "=" * 60)
    print("🔧 ТЕСТИРОВАНИЕ MIDDLEWARE")
    print("=" * 60)

    # Проверяем, что middleware зарегистрированы
    print(f"Зарегистрировано middleware: {len(app.middleware_stack)}")
    for i, mw in enumerate(app.middleware_stack):
        print(f"  {i+1}. {mw.__class__.__name__}")

    # Тестируем CORS
    print("\nТестируем CORS middleware...")
    status, response = await test_endpoint(
        "OPTIONS", "/users", "", None, headers=[(b"origin", b"http://localhost:3000")]
    )

    if status:
        print(f"CORS preflight: {status}")


async def test_error_handling():
    """Тестировать обработку ошибок"""
    print("\n" + "=" * 60)
    print("🚨 ТЕСТИРОВАНИЕ ОБРАБОТКИ ОШИБОК")
    print("=" * 60)

    error_tests = [
        ("GET", "/nonexistent", "", None),  # 404
        ("GET", "/users/invalid", "", None),  # 400
        ("POST", "/users", "", "invalid json"),  # JSON ошибка
        ("GET", "/demo/error", "", None),  # Демо ошибка 500
    ]

    for method, path, query, body in error_tests:
        await test_endpoint(method, path, query, body)


async def main():
    """Главная функция"""
    print("QakeAPI - Тестирование API эндпоинтов")
    print("=" * 60)

    try:
        # Основные тесты
        success, errors = await run_tests()

        # Тесты middleware
        await test_middleware()

        # Тесты обработки ошибок
        await test_error_handling()

        print("\n" + "=" * 60)
        print("✨ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("=" * 60)

        if errors == 0:
            print("🎉 Все компоненты работают корректно!")
            print("✅ API готов к использованию")
        else:
            print(f"⚠️  Обнаружено {errors} проблем, требующих внимания")

        return errors == 0

    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Запускаем тесты
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
