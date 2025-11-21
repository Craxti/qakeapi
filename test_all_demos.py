"""
Скрипт для проверки всех демо приложений и их эндпоинтов
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import httpx

# Устанавливаем UTF-8 для вывода
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


async def test_endpoint(client: httpx.AsyncClient, method: str, url: str, **kwargs):
    """Тестирует один эндпоинт"""
    try:
        response = await client.request(method, url, timeout=5.0, **kwargs)
        return {
            "status": response.status_code,
            "success": 200 <= response.status_code < 300,
            "headers": dict(response.headers),
            "body": response.text[:200] if response.text else None,
        }
    except Exception as e:
        return {
            "status": None,
            "success": False,
            "error": str(e),
        }


async def test_working_demo():
    """Тестирует working_demo.py"""
    print("\n" + "=" * 80)
    print("ТЕСТИРОВАНИЕ: examples/working_demo.py")
    print("=" * 80)
    
    base_url = "http://127.0.0.1:8000"
    results = {}
    
    async with httpx.AsyncClient() as client:
        # Проверяем доступность сервера
        try:
            await client.get(f"{base_url}/health", timeout=2.0)
        except Exception as e:
            print(f"[ERROR] Сервер не запущен на порту 8000: {e}")
            return {"status": "server_not_running", "endpoints": {}}
        
        endpoints = [
            ("GET", "/", "Главная страница"),
            ("GET", "/health", "Проверка здоровья"),
            ("GET", "/items", "Список товаров"),
            ("GET", "/items/1", "Товар по ID"),
            ("GET", "/items/999", "Несуществующий товар"),
            ("GET", "/large", "Большой ответ"),
            ("GET", "/docs", "OpenAPI документация"),
            ("POST", "/items", "Создать товар", {"json": {"name": "Тест", "price": 1000}}),
        ]
        
        for endpoint in endpoints:
            method = endpoint[0]
            path = endpoint[1]
            name = endpoint[2]
            kwargs = endpoint[3] if len(endpoint) > 3 else {}
            
            result = await test_endpoint(client, method, f"{base_url}{path}", **kwargs)
            results[path] = {
                "method": method,
                "name": name,
                **result
            }
            
            status_icon = "[OK]" if result["success"] else "[FAIL]"
            print(f"{status_icon} {method:6} {path:30} - {name}")
            if not result["success"]:
                error_msg = result.get('error') or f"Status: {result.get('status')}"
                print(f"   Ошибка: {error_msg}")
    
    return {"status": "completed", "endpoints": results}


async def test_comprehensive_demo():
    """Тестирует comprehensive_demo.py"""
    print("\n" + "=" * 80)
    print("ТЕСТИРОВАНИЕ: examples/comprehensive_demo.py")
    print("=" * 80)
    
    base_url = "http://127.0.0.1:8001"
    results = {}
    
    async with httpx.AsyncClient() as client:
        try:
            await client.get(f"{base_url}/", timeout=2.0)
        except Exception as e:
            print(f"[ERROR] Сервер не запущен на порту 8001: {e}")
            return {"status": "server_not_running", "endpoints": {}}
        
        endpoints = [
            ("GET", "/", "Главная страница"),
            ("GET", "/users", "Список пользователей"),
            ("GET", "/users/1", "Пользователь по ID"),
            ("POST", "/users", "Создать пользователя", {
                "json": {"name": "Test User", "email": "test@example.com", "age": 25}
            }),
            ("GET", "/items", "Список товаров"),
            ("GET", "/docs", "OpenAPI документация"),
        ]
        
        for endpoint in endpoints:
            method = endpoint[0]
            path = endpoint[1]
            name = endpoint[2]
            kwargs = endpoint[3] if len(endpoint) > 3 else {}
            
            result = await test_endpoint(client, method, f"{base_url}{path}", **kwargs)
            results[path] = {
                "method": method,
                "name": name,
                **result
            }
            
            status_icon = "[OK]" if result["success"] else "[FAIL]"
            print(f"{status_icon} {method:6} {path:30} - {name}")
            if not result["success"]:
                error_msg = result.get('error') or f"Status: {result.get('status')}"
                print(f"   Ошибка: {error_msg}")
    
    return {"status": "completed", "endpoints": results}


async def main():
    """Главная функция"""
    print("\n" + "=" * 80)
    print("ПРОВЕРКА ВСЕХ ДЕМО ПРИЛОЖЕНИЙ QakeAPI")
    print("=" * 80)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = {}
    
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
        
        print(f"\n📊 {app_name}:")
        print(f"   Всего эндпоинтов: {app_total}")
        print(f"   ✅ Успешно: {app_success}")
        print(f"   ❌ Ошибок: {app_failed}")
        
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
    print(f"✅ Успешно: {successful_endpoints}")
    print(f"❌ Ошибок: {failed_endpoints}")
    print(f"Процент успеха: {(successful_endpoints/total_endpoints*100) if total_endpoints > 0 else 0:.1f}%")
    
    # Сохраняем отчет в файл
    report_file = Path("demo_test_report.json")
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
    
    print(f"\n📄 Подробный отчет сохранен в: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())

