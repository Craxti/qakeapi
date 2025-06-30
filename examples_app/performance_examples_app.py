#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance examples launcher for QakeAPI.
"""
import sys
import os
import subprocess
import time

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Performance examples list
PERFORMANCE_APPS = [
    "caching_app.py",
    "profiling_app.py",
    "optimization_app.py"
]

# Port mapping for performance apps
PERFORMANCE_PORTS = {
    "caching_app.py": 8005,
    "profiling_app.py": 8012,
    "optimization_app.py": 8017
}

def start_performance_apps():
    """Start all performance example applications"""
    print("⚡ Starting QakeAPI Performance Examples")
    print("=" * 40)
    
    processes = []
    
    for app in PERFORMANCE_APPS:
        port = PERFORMANCE_PORTS[app]
        print(f"Starting {app} on port {port}...")
        
        try:
            process = subprocess.Popen(
                [sys.executable, app],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            processes.append((app, process, port))
            time.sleep(2)  # Wait for startup
        except Exception as e:
            print(f"❌ Failed to start {app}: {e}")
    
    print("\n✅ Performance examples started:")
    for app, process, port in processes:
        print(f"  • {app} - http://localhost:{port}")
    
    return processes

if __name__ == "__main__":
    start_performance_apps() 