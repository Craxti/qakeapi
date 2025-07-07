#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic startup of all QakeAPI examples.
"""
import sys
import os
import subprocess
import time
import signal
import psutil

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# List of all example applications
APPS = [
    "basic_crud_app.py",
    "websocket_app.py", 
    "background_tasks_app.py",
    "rate_limit_app.py",
    "caching_app.py",
    "auth_app.py",
    "file_upload_app.py",
    "validation_app.py",
    "jwt_auth_app.py",
    "middleware_app.py",
    "dependency_injection_app.py",
    "profiling_app.py",
    "openapi_app.py",
    "csrf_app.py",
    "xss_app.py",
    "sql_injection_app.py",
    "optimization_app.py",
    "advanced_testing_app.py",
    "live_reload_app.py",
    "api_versioning_app.py",
    "websocket_enhanced_app.py",
    "websocket_clustered_app.py",
    "enhanced_documentation_app.py",
    "security_examples_app.py",
    "performance_examples_app.py",
    "template_app.py",
    "enhanced_testing_example.py",
    "api_versioning_enhanced_app.py",
    "graphql_app.py",
    "event_driven_app.py"
]

# Port mapping for each app
PORT_MAPPING = {
    "basic_crud_app.py": 8001,
    "websocket_app.py": 8002,
    "background_tasks_app.py": 8003,
    "rate_limit_app.py": 8004,
    "caching_app.py": 8005,
    "auth_app.py": 8006,
    "file_upload_app.py": 8007,
    "validation_app.py": 8008,
    "jwt_auth_app.py": 8009,
    "middleware_app.py": 8010,
    "dependency_injection_app.py": 8011,
    "profiling_app.py": 8012,
    "openapi_app.py": 8013,
    "csrf_app.py": 8014,
    "xss_app.py": 8015,
    "sql_injection_app.py": 8016,
    "optimization_app.py": 8017,
    "advanced_testing_app.py": 8018,
    "live_reload_app.py": 8019,
    "api_versioning_app.py": 8020,
    "websocket_enhanced_app.py": 8021,
    "websocket_clustered_app.py": 8022,
    "enhanced_documentation_app.py": 8023,
    "security_examples_app.py": 8024,
    "performance_examples_app.py": 8025,
    "template_app.py": 8026,
    "enhanced_testing_example.py": 8027,
    "api_versioning_enhanced_app.py": 8028,
    "graphql_app.py": 8030,
    "event_driven_app.py": 8040
}

def check_port_available(port):
    """Check if port is available"""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def kill_process_on_port(port):
    """Kill process using specified port"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            connections = proc.net_connections()
            for conn in connections:
                if hasattr(conn, 'laddr') and conn.laddr.port == port:
                    print(f"Killing process {proc.info['pid']} on port {port}")
                    proc.kill()
                    time.sleep(1)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def start_app(app_name):
    """Start single application"""
    port = PORT_MAPPING[app_name]
    
    # Check if port is available
    if not check_port_available(port):
        print(f"Port {port} is busy, killing existing process...")
        kill_process_on_port(port)
        time.sleep(5)  # Увеличенная задержка
    
    # Повторные попытки запуска
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        if not check_port_available(port):
            print(f"[Attempt {attempt}] Port {port} still busy, waiting...")
            time.sleep(2)
            continue
        try:
            # Set environment variable for Python path
            env = os.environ.copy()
            qakeapi_path = os.path.join(os.path.dirname(__file__), '..')
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = qakeapi_path + os.pathsep + env['PYTHONPATH']
            else:
                env['PYTHONPATH'] = qakeapi_path
            
            process = subprocess.Popen(
                [sys.executable, app_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env
            )
            time.sleep(3)
            if process.poll() is None:
                print(f"✅ {app_name} started on port {port} (PID: {process.pid})")
                return process
            else:
                print(f"❌ {app_name} failed to start on port {port}")
                return None
        except Exception as e:
            print(f"❌ Error starting {app_name}: {e}")
            return None
    print(f"❌ {app_name} could not start after {max_attempts} attempts (port {port} still busy)")
    return None

def stop_all_apps():
    """Stop all running applications"""
    print("Stopping all applications...")
    
    # Kill processes by name
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] == 'python' or proc.info['name'] == 'python3':
                cmdline = proc.cmdline()
                if any(app in cmdline for app in APPS):
                    print(f"Killing process {proc.info['pid']}: {cmdline}")
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Kill processes by port
    for port in PORT_MAPPING.values():
        kill_process_on_port(port)
    
    print("All applications stopped")

def main():
    """Main function"""
    print("🚀 Starting all QakeAPI example applications")
    print("=" * 50)
    
    # Stop any existing applications
    stop_all_apps()
    time.sleep(2)
    
    processes = []
    started_count = 0
    
    # Start all applications
    for app in APPS:
        print(f"Starting {app}...")
        process = start_app(app)
        if process:
            processes.append((app, process))
            started_count += 1
        else:
            print(f"Failed to start {app}")
    
    print("\n" + "=" * 50)
    print(f"📊 Startup Summary:")
    print(f"✅ Successfully started: {started_count}/{len(APPS)} applications")
    
    if started_count == len(APPS):
        print("🎉 All applications started successfully!")
    else:
        print("⚠️ Some applications failed to start")
    
    print("\n📋 Running applications:")
    for app, process in processes:
        port = PORT_MAPPING[app]
        print(f"  • {app} - http://localhost:{port} (PID: {process.pid})")
    
    print("\n💡 To stop all applications, press Ctrl+C")
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
            # Check if any processes died
            for app, process in processes[:]:
                if process.poll() is not None:
                    print(f"⚠️ {app} unexpectedly stopped")
                    processes.remove((app, process))
            
    except KeyboardInterrupt:
        print("\n\n🛑 Received interrupt signal")
        stop_all_apps()
        print("All applications stopped")

if __name__ == "__main__":
    main() 