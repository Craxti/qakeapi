"""
Полный скрипт для проверки всех демо приложений и их эндпоинтов
"""
import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

# Устанавливаем UTF-8 для вывода
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


async def test_endpoint(client: httpx.AsyncClient, method: str, url: str, expected_status=None, **kwargs):
    """Тестирует один эндпоинт"""
    try:
        response = await client.request(method, url, timeout=5.0, **kwargs)
        success = True
        if expected_status:
            success = response.status_code == expected_status
        else:
            success = 200 <= response.status_code < 300
        
        return {
            "status": response.status_code,
            "success": success,
            "expected_status": expected_status,
            "headers": dict(response.headers),
            "body": response.text[:200] if response.text else None,
        }
    except Exception as e:
        return {
            "status": None,
            "success": False,
            "error": str(e),
        }


async def test_app(base_url, port, app_name, endpoints_config):
    """Тестирует одно приложение"""
    print("\n" + "=" * 80)
    print(f"ТЕСТИРОВАНИЕ: {app_name}")
    print("=" * 80)
    
    results = {}
    
    async with httpx.AsyncClient() as client:
        # Проверяем доступность сервера
        try:
            await client.get(f"{base_url}/", timeout=2.0)
        except Exception as e:
            print(f"[ERROR] Сервер не запущен на порту {port}: {e}")
            return {"status": "server_not_running", "endpoints": {}}
        
        for endpoint_config in endpoints_config:
            method = endpoint_config[0]
            path = endpoint_config[1]
            name = endpoint_config[2]
            kwargs = endpoint_config[3] if len(endpoint_config) > 3 else {}
            expected_status = endpoint_config[4] if len(endpoint_config) > 4 else None
            
            result = await test_endpoint(client, method, f"{base_url}{path}", expected_status, **kwargs)
            results[path] = {
                "method": method,
                "name": name,
                **result
            }
            
            status_icon = "[OK]" if result["success"] else "[FAIL]"
            status_info = f" (ожидался {expected_status})" if expected_status else ""
            print(f"{status_icon} {method:6} {path:40} - {name}{status_info}")
            if not result["success"]:
                error_msg = result.get('error') or f"Status: {result.get('status')}"
                print(f"   Ошибка: {error_msg}")
    
    return {"status": "completed", "endpoints": results}


async def test_working_demo():
    """Тестирует working_demo.py"""
    endpoints = [
        ("GET", "/", "Главная страница"),
        ("GET", "/health", "Проверка здоровья"),
        ("GET", "/items", "Список товаров"),
        ("GET", "/items/1", "Товар по ID"),
        ("GET", "/items/999", "Несуществующий товар", {}, 404),  # Ожидаем 404
        ("GET", "/large", "Большой ответ"),
        ("GET", "/docs", "OpenAPI документация"),
        ("POST", "/items", "Создать товар", {"json": {"name": "Тест", "price": 1000}}),
    ]
    return await test_app("http://127.0.0.1:8000", 8000, "examples/working_demo.py", endpoints)


async def test_comprehensive_demo():
    """Тестирует comprehensive_demo.py"""
    endpoints = [
        ("GET", "/", "Главная страница"),
        ("GET", "/health", "Проверка здоровья"),
        ("GET", "/users", "Список пользователей"),
        ("GET", "/users/1", "Пользователь по ID"),
        ("GET", "/users/999", "Несуществующий пользователь", {}, 404),
        ("POST", "/users", "Создать пользователя", {
            "json": {"name": "Test User", "email": "test@example.com", "age": 25}
        }),
        ("GET", "/items", "Список товаров"),
        ("GET", "/items/1", "Товар по ID"),
        ("POST", "/items", "Создать товар", {
            "json": {"name": "Test Item", "price": 100.0, "description": "Test"}
        }),
        ("GET", "/docs", "OpenAPI документация"),
    ]
    return await test_app("http://127.0.0.1:8001", 8001, "examples/comprehensive_demo.py", endpoints)


async def main():
    """Главная функция"""
    print("\n" + "=" * 80)
    print("ПОЛНАЯ ПРОВЕРКА ВСЕХ ДЕМО ПРИЛОЖЕНИЙ QakeAPI")
    print("=" * 80)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = {}
    processes = []
    
    # Запускаем серверы
    print("\n[INFO] Запуск демо серверов...")
    
    # Working demo на порту 8000
    print("  - Запуск working_demo на порту 8000...")
    process1 = subprocess.Popen(
        [sys.executable, "examples/working_demo.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    processes.append(("working_demo", process1, 8000))
    
    # Comprehensive demo на порту 8001
    print("  - Запуск comprehensive_demo на порту 8001...")
    # Модифицируем comprehensive_demo для запуска на другом порту
    process2 = subprocess.Popen(
        [sys.executable, "-c", 
         "import sys; sys.path.insert(0, 'examples'); "
         "from comprehensive_demo import app; "
         "import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8001)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    processes.append(("comprehensive_demo", process2, 8001))
    
    # Ждем запуска серверов
    print("\n[INFO] Ожидание запуска серверов (7 секунд)...")
    await asyncio.sleep(7)
    
    try:
        # Тестируем working_demo
        all_results["working_demo"] = await test_working_demo()
        
        # Тестируем comprehensive_demo
        all_results["comprehensive_demo"] = await test_comprehensive_demo()
        
        # Создаем итоговый отчет
        print("\n" + "=" * 80)
        print("ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 80)
        
        total_endpoints = 0
        successful_endpoints = 0
        failed_endpoints = 0
        
        for app_name, app_results in all_results.items():
            if app_results["status"] == "server_not_running":
                print(f"\n[ERROR] {app_name}: Сервер не запущен")
                continue
            
            endpoints = app_results.get("endpoints", {})
            app_success = sum(1 for e in endpoints.values() if e.get("success"))
            app_total = len(endpoints)
            app_failed = app_total - app_success
            
            total_endpoints += app_total
            successful_endpoints += app_success
            failed_endpoints += app_failed
            
            print(f"\n[REPORT] {app_name}:")
            print(f"   Всего эндпоинтов: {app_total}")
            print(f"   [OK] Успешно: {app_success}")
            print(f"   [FAIL] Ошибок: {app_failed}")
            
            if app_failed > 0:
                print("   Проблемные эндпоинты:")
                for path, endpoint in endpoints.items():
                    if not endpoint.get("success"):
                        error_info = endpoint.get('error') or f"Status {endpoint.get('status')}"
                        print(f"      - {endpoint['method']} {path}: {error_info}")
        
        print("\n" + "=" * 80)
        print("ОБЩАЯ СТАТИСТИКА")
        print("=" * 80)
        print(f"Всего эндпоинтов протестировано: {total_endpoints}")
        print(f"[OK] Успешно: {successful_endpoints}")
        print(f"[FAIL] Ошибок: {failed_endpoints}")
        if total_endpoints > 0:
            print(f"Процент успеха: {(successful_endpoints/total_endpoints*100):.1f}%")
        
        # Сохраняем отчет в файл
        report_file = Path("demo_test_report_complete.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": all_results,
                "summary": {
                    "total": total_endpoints,
                    "successful": successful_endpoints,
                    "failed": failed_endpoints,
                }
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n[INFO] Подробный отчет сохранен в: {report_file}")
        
    finally:
        # Останавливаем серверы
        print("\n[INFO] Остановка серверов...")
        for name, process, port in processes:
            try:
                process.terminate()
                process.wait(timeout=3)
                print(f"  - {name} (порт {port}) остановлен")
            except:
                process.kill()
                print(f"  - {name} (порт {port}) принудительно остановлен")


if __name__ == "__main__":
    asyncio.run(main())

