#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security examples launcher for QakeAPI.
"""
import sys
import os
import subprocess
import time

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Security examples list
SECURITY_APPS = [
    "csrf_app.py",
    "xss_app.py", 
    "sql_injection_app.py"
]

# Port mapping for security apps
SECURITY_PORTS = {
    "csrf_app.py": 8014,
    "xss_app.py": 8015,
    "sql_injection_app.py": 8016
}

def start_security_apps():
    """Start all security example applications"""
    print("🔒 Starting QakeAPI Security Examples")
    print("=" * 40)
    
    processes = []
    
    for app in SECURITY_APPS:
        port = SECURITY_PORTS[app]
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
    
    print("\n✅ Security examples started:")
    for app, process, port in processes:
        print(f"  • {app} - http://localhost:{port}")
    
    return processes

if __name__ == "__main__":
    start_security_apps() 