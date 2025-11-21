"""
Скрипт для запуска демо сервера
"""
import subprocess
import sys
import time
import os

def start_server(script_path, port):
    """Запускает сервер в отдельном процессе"""
    print(f"Запуск сервера: {script_path} на порту {port}")
    process = subprocess.Popen(
        [sys.executable, script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )
    time.sleep(3)  # Даем серверу время на запуск
    return process

if __name__ == "__main__":
    # Запускаем working_demo на порту 8000
    print("Запуск демо приложений...")
    process1 = start_server("examples/working_demo.py", 8000)
    print(f"Working demo запущен (PID: {process1.pid})")
    print("Нажмите Ctrl+C для остановки")
    
    try:
        process1.wait()
    except KeyboardInterrupt:
        print("\nОстановка серверов...")
        process1.terminate()
        process1.wait()

