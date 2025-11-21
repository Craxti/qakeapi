#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic testing of all QakeAPI examples.
"""
import sys
import os
import asyncio
import aiohttp
import time
import json
from datetime import datetime
import random
import string

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test configuration
TEST_CONFIG = {
    "basic_crud_app": {"port": 8001, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/users", "expected_status": 200},
        {"method": "POST", "path": "/users", "data": {"username": "testuser9", "email": "test9@example.com", "password": "testpass123"}, "expected_status": 200}
    ]},
    "websocket_app": {"port": 8002, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/stats", "expected_status": 200},
        {"method": "POST", "path": "/broadcast", "data": {"message": "test broadcast"}, "expected_status": 200}
    ]},
    "background_tasks_app": {"port": 8003, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/tasks", "expected_status": 200},
        {"method": "GET", "path": "/stats", "expected_status": 200}
    ]},
    "rate_limit_app": {"port": 8004, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/normal", "expected_status": 200},
        {"method": "GET", "path": "/strict", "expected_status": 200},
        {"method": "GET", "path": "/burst", "expected_status": 200},
        {"method": "GET", "path": "/stats", "expected_status": 200}
    ]},
    "caching_app": {"port": 8005, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/compute/5", "expected_status": 200},
        {"method": "GET", "path": "/cache", "expected_status": 200}
    ]},
    "auth_app": {"port": 8006, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "POST", "path": "/login", "data": {"username": "admin", "password": "admin123"}, "expected_status": 200},
        {"method": "GET", "path": "/protected", "expected_status": 401}
    ]},
    "file_upload_app": {"port": 8007, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/files", "expected_status": 200},
        {"method": "GET", "path": "/stats", "expected_status": 200}
    ]},
    "validation_app": {"port": 8008, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "POST", "path": "/users", "data": {"username": "testuser10", "email": "test10@example.com", "password": "TestPass123"}, "expected_status": 200},
        {"method": "GET", "path": "/users/999", "expected_status": 404},
        {"method": "GET", "path": "/search?query=test", "expected_status": 200}
    ]},
    "jwt_auth_app": {"port": 8009, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/public", "expected_status": 200},
        {"method": "GET", "path": "/protected", "expected_status": 401}
    ]},
    "middleware_app": {"port": 8010, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/public", "expected_status": 200},
        {"method": "GET", "path": "/protected", "expected_status": 200},
        {"method": "GET", "path": "/health", "expected_status": 200}
    ]},
    "dependency_injection_app": {"port": 8011, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "POST", "path": "/users", "data": {"username": "testuser", "email": "test@example.com"}, "expected_status": 200},
        {"method": "GET", "path": "/dependencies", "expected_status": 200}
    ]},
    "profiling_app": {"port": 8012, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/fast", "expected_status": 200},
        {"method": "GET", "path": "/medium", "expected_status": 200}
    ]},
    "openapi_app": {"port": 8013, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/users?page=1&size=10", "expected_status": 200},
        {"method": "GET", "path": "/products?page=1&size=10", "expected_status": 200},
        {"method": "GET", "path": "/orders?page=1&size=10", "expected_status": 200},
        {"method": "GET", "path": "/health", "expected_status": 200}
    ]},
    "csrf_app": {"port": 8014, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/profile", "expected_status": 401},
        {"method": "GET", "path": "/csrf-token", "expected_status": 401}
    ]},
    "xss_app": {"port": 8015, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "POST", "path": "/comments", "data": {"author": "testuser", "content": "test comment"}, "expected_status": 200},
        {"method": "GET", "path": "/test-xss", "expected_status": 200}
    ]},
    "sql_injection_app": {"port": 8016, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "POST", "path": "/users", "data": {"username": "testuser11", "email": "test11@example.com", "password": "testpass123"}, "expected_status": 200},
        {"method": "POST", "path": "/products", "data": {"name": "testproduct", "price": 10.0, "category": "test"}, "expected_status": 200}
    ]},
    "optimization_app": {"port": 8017, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/cache-test", "expected_status": 200},
        {"method": "GET", "path": "/async-operations", "expected_status": 200}
    ]},
    "live_reload_app": {"port": 8019, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/about", "expected_status": 200},
        {"method": "GET", "path": "/dynamic", "expected_status": 200},
        {"method": "GET", "path": "/api/info", "expected_status": 200},
        {"method": "GET", "path": "/health", "expected_status": 200}
    ]},
    "advanced_testing_app": {"port": 8018, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/users", "expected_status": 200},
        {"method": "GET", "path": "/products", "expected_status": 200},
        {"method": "GET", "path": "/orders", "expected_status": 200},
        {"method": "GET", "path": "/performance", "expected_status": 200},
        {"method": "GET", "path": "/chaos", "expected_status": 200},
        {"method": "GET", "path": "/concurrent", "expected_status": 200},
        {"method": "GET", "path": "/memory", "expected_status": 200},
        {"method": "GET", "path": "/test-report", "expected_status": 200}
    ]},
    "api_versioning_app": {"port": 8020, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/v1/users", "expected_status": 200},
        {"method": "GET", "path": "/v2/users", "expected_status": 200},
        {"method": "GET", "path": "/v3/users", "expected_status": 200},
        {"method": "GET", "path": "/api/versions", "expected_status": 200},
        {"method": "GET", "path": "/api/changelog", "expected_status": 200},
        {"method": "GET", "path": "/api/deprecations", "expected_status": 200}
    ]},
    "websocket_enhanced_app": {"port": 8021, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/api/connections", "expected_status": 200},
        {"method": "GET", "path": "/api/broadcast", "expected_status": 200},
        {"method": "GET", "path": "/api/rooms", "expected_status": 200}
    ]},
    "enhanced_documentation_app": {"port": 8022, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/docs", "expected_status": 200},
        {"method": "GET", "path": "/openapi.json", "expected_status": 200},
        {"method": "GET", "path": "/users", "expected_status": 200},
        {"method": "GET", "path": "/messages", "expected_status": 200}
    ]},
    "security_examples_app": {"port": 8023, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/security-info", "expected_status": 200},
        {"method": "GET", "path": "/validation-test", "expected_status": 200},
        {"method": "GET", "path": "/encoding-test", "expected_status": 200}
    ]},
    "performance_examples_app": {"port": 8024, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/performance-info", "expected_status": 200},
        {"method": "GET", "path": "/cache-test", "expected_status": 200},
        {"method": "GET", "path": "/async-test", "expected_status": 200},
        {"method": "GET", "path": "/benchmark", "expected_status": 200}
    ]},
    "template_app": {"port": 8025, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/users", "expected_status": 200},
        {"method": "GET", "path": "/user/1", "expected_status": 200},
        {"method": "GET", "path": "/string", "expected_status": 200},
        {"method": "GET", "path": "/debug", "expected_status": 200}
    ]},
    "enhanced_testing_example": {"port": 8026, "tests": [
        {"method": "GET", "path": "/", "expected_status": 200},
        {"method": "GET", "path": "/users", "expected_status": 200},
        {"method": "GET", "path": "/users/1", "expected_status": 200},
        {"method": "GET", "path": "/posts", "expected_status": 200}
    ]}
}

async def test_endpoint(session, url, method="GET", data=None, headers=None, expected_status=200):
    """Test single endpoint"""
    try:
        if method == "GET":
            async with session.get(url, headers=headers) as response:
                return response.status == expected_status, await response.text()
        elif method == "POST":
            async with session.post(url, json=data, headers=headers) as response:
                return response.status == expected_status, await response.text()
        elif method == "PUT":
            async with session.put(url, json=data, headers=headers) as response:
                return response.status == expected_status, await response.text()
        elif method == "DELETE":
            async with session.delete(url, headers=headers) as response:
                return response.status == expected_status, await response.text()
    except Exception as e:
        return False, str(e)

def random_user():
    """Generate random user data"""
    suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    return {
        "username": f"testuser{suffix}",
        "email": f"test{suffix}@example.com",
        "password": "TestPass123"
    }

async def main():
    """Main testing function"""
    print("🚀 Starting automatic testing of all QakeAPI examples")
    print("=" * 60)
    
    total_passed = 0
    total_tests = 0
    
    async with aiohttp.ClientSession() as session:
        for app_name, config in TEST_CONFIG.items():
            print(f"\n📋 Testing {app_name} (port {config['port']})")
            print("-" * 40)
            
            # Wait a bit for app startup
            await asyncio.sleep(1)
            
            try:
                base_url = f"http://127.0.0.1:{config['port']}"
                
                # Test each endpoint from configuration
                passed = 0
                total = len(config['tests'])
                
                for test in config['tests']:
                    method = test['method']
                    path = test['path']
                    data = test.get('data')
                    expected_status = test['expected_status']

                    # If test creates user, use unique data
                    if method == "POST" and "/users" in path and data and "username" in data:
                        data = random_user()
                    
                    success, response = await test_endpoint(
                        session, 
                        f"{base_url}{path}", 
                        method, 
                        data, 
                        None, 
                        expected_status
                    )
                    
                    if success:
                        passed += 1
                        print(f"  ✅ {method} {path}")
                    else:
                        print(f"  ❌ {method} {path} - {response}")
                
                total_passed += passed
                total_tests += total
                
                if passed == total:
                    print(f"✅ {app_name}: {passed}/{total} tests passed")
                else:
                    print(f"⚠️ {app_name}: {passed}/{total} tests passed")
                    
            except Exception as e:
                print(f"❌ {app_name}: Testing error - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS:")
    print(f"✅ Tests passed: {total_passed}/{total_tests}")
    print(f"📈 Success rate: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "📈 Success rate: 0%")
    
    if total_passed == total_tests:
        print("🎉 All tests passed successfully!")
    else:
        print("⚠️ Some tests failed")

if __name__ == "__main__":
    asyncio.run(main()) 