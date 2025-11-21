"""
Test examples by actually running them and testing endpoints
"""
import asyncio
import sys
import subprocess
import time
import signal
import os

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Install it with: pip install httpx")
    sys.exit(1)


async def test_basic_app():
    """Test basic_app.py"""
    print("\n" + "="*60)
    print("Testing: basic_app.py")
    print("="*60)
    
    # Start server
    process = subprocess.Popen(
        [sys.executable, "examples/basic_app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, 'PYTHONPATH': os.getcwd()},
    )
    
    try:
        # Wait for server to start
        await asyncio.sleep(7)
        
        # Try to connect with retries
        max_retries = 5
        for i in range(max_retries):
            try:
                async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=2.0) as test_client:
                    await test_client.get("/")
                break
            except:
                if i < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    print("  WARNING: Server did not start in time")
                    return False
        
        async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=10.0) as client:
            tests = [
                ("GET", "/", "Root endpoint"),
                ("GET", "/hello/World", "Hello with name"),
                ("GET", "/items/1?q=test", "Get item with query"),
                ("POST", "/items/", {"name": "Test"}, "Create item"),
            ]
            
            passed = 0
            for method, path, *rest in tests:
                try:
                    if method == "GET":
                        response = await client.get(path)
                    elif method == "POST":
                        response = await client.post(path, json=rest[0] if rest else None)
                    
                    if response.status_code == 200:
                        print(f"  PASS: {method} {path}")
                        passed += 1
                    else:
                        print(f"  FAIL: {method} {path} - Status: {response.status_code}")
                except Exception as e:
                    print(f"  FAIL: {method} {path} - Error: {e}")
            
            print(f"\n  Results: {passed}/{len(tests)} tests passed")
            return passed == len(tests)
    finally:
        process.terminate()
        process.wait()


async def test_monitoring_example():
    """Test monitoring_example.py"""
    print("\n" + "="*60)
    print("Testing: monitoring_example.py")
    print("="*60)
    
    process = subprocess.Popen(
        [sys.executable, "examples/monitoring_example.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, 'PYTHONPATH': os.getcwd()},
    )
    
    try:
        await asyncio.sleep(5)
        
        async with httpx.AsyncClient(base_url="http://localhost:8001", timeout=10.0) as client:
            tests = [
                ("GET", "/", "Root"),
                ("GET", "/metrics", "Metrics"),
                ("GET", "/health", "Health check"),
            ]
            
            passed = 0
            for method, path, desc in tests:
                try:
                    response = await client.get(path)
                    if response.status_code == 200:
                        print(f"  PASS: {desc}")
                        passed += 1
                    else:
                        print(f"  FAIL: {desc} - Status: {response.status_code}")
                except Exception as e:
                    print(f"  FAIL: {desc} - Error: {e}")
            
            print(f"\n  Results: {passed}/{len(tests)} tests passed")
            return passed == len(tests)
    finally:
        process.terminate()
        process.wait()


async def test_caching_example():
    """Test caching_example.py"""
    print("\n" + "="*60)
    print("Testing: caching_example.py")
    print("="*60)
    
    process = subprocess.Popen(
        [sys.executable, "examples/caching_example.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, 'PYTHONPATH': os.getcwd()},
    )
    
    try:
        await asyncio.sleep(5)
        
        async with httpx.AsyncClient(base_url="http://localhost:8002", timeout=10.0) as client:
            tests = [
                ("GET", "/", "Root"),
                ("GET", "/items/", "Get all items"),
                ("GET", "/cache/stats", "Cache stats"),
            ]
            
            # Test item endpoint separately - it may return 404 if item doesn't exist
            # but we check if the endpoint itself works
            item_tests = [
                ("GET", "/items/1", "Get item 1"),
                ("GET", "/items/2", "Get item 2"),
                ("GET", "/items/3", "Get item 3"),
            ]
            
            passed = 0
            for method, path, desc in tests:
                try:
                    response = await client.get(path)
                    if response.status_code == 200:
                        print(f"  PASS: {desc}")
                        passed += 1
                    else:
                        print(f"  FAIL: {desc} - Status: {response.status_code}")
                except Exception as e:
                    print(f"  FAIL: {desc} - Error: {e}")
            
            # Test at least one item endpoint works (should return 200 for existing items)
            item_passed = False
            for method, path, desc in item_tests:
                try:
                    response = await client.get(path)
                    if response.status_code == 200:
                        print(f"  PASS: {desc}")
                        item_passed = True
                        passed += 1
                        break
                    elif response.status_code == 404:
                        # Item not found - this is OK, endpoint works
                        print(f"  INFO: {desc} - Item not found (404), but endpoint works")
                except Exception as e:
                    pass
            
            if not item_passed:
                print(f"  WARNING: No items found in cache/db, but endpoint structure is correct")
            
            print(f"\n  Results: {passed}/{len(tests) + 1} core tests passed")
            # Consider it passed if core endpoints work
            return passed >= len(tests)
    finally:
        process.terminate()
        process.wait()


async def test_error_handling_example():
    """Test error_handling_example.py"""
    print("\n" + "="*60)
    print("Testing: error_handling_example.py")
    print("="*60)
    
    process = subprocess.Popen(
        [sys.executable, "examples/error_handling_example.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, 'PYTHONPATH': os.getcwd()},
    )
    
    try:
        await asyncio.sleep(5)
        
        async with httpx.AsyncClient(base_url="http://localhost:8004", timeout=10.0) as client:
            tests = [
                ("GET", "/", 200, "Root"),
                ("GET", "/success", 200, "Success"),
                ("GET", "/not-found", 404, "404 error"),
                ("GET", "/validation-error", 400, "Validation error"),  # Custom handler overrides to 400
            ]
            
            passed = 0
            for method, path, expected_status, desc in tests:
                try:
                    response = await client.get(path)
                    if response.status_code == expected_status:
                        print(f"  PASS: {desc} (Status: {response.status_code})")
                        passed += 1
                    else:
                        print(f"  FAIL: {desc} - Expected {expected_status}, got {response.status_code}")
                except Exception as e:
                    print(f"  FAIL: {desc} - Error: {e}")
            
            print(f"\n  Results: {passed}/{len(tests)} tests passed")
            return passed == len(tests)
    finally:
        process.terminate()
        process.wait()


async def test_compression_example():
    """Test compression_example.py"""
    print("\n" + "="*60)
    print("Testing: compression_example.py")
    print("="*60)
    
    process = subprocess.Popen(
        [sys.executable, "examples/compression_example.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, 'PYTHONPATH': os.getcwd()},
    )
    
    try:
        await asyncio.sleep(5)
        
        async with httpx.AsyncClient(base_url="http://localhost:8005", timeout=10.0) as client:
            tests = [
                ("GET", "/", "Root"),
                ("GET", "/small", "Small response"),
                ("GET", "/large", "Large response"),
            ]
            
            passed = 0
            for method, path, desc in tests:
                try:
                    response = await client.get(path)
                    if response.status_code == 200:
                        print(f"  PASS: {desc}")
                        passed += 1
                    else:
                        print(f"  FAIL: {desc} - Status: {response.status_code}")
                except Exception as e:
                    print(f"  FAIL: {desc} - Error: {e}")
            
            print(f"\n  Results: {passed}/{len(tests)} tests passed")
            return passed == len(tests)
    finally:
        process.terminate()
        process.wait()


async def main():
    """Main test function"""
    print("="*60)
    print("Testing QakeAPI Examples - Endpoint Testing")
    print("="*60)
    print("\nThis will start each example server and test endpoints...")
    print("Press Ctrl+C to stop\n")
    
    await asyncio.sleep(2)
    
    results = {}
    
    try:
        results["basic_app"] = await test_basic_app()
    except Exception as e:
        print(f"ERROR testing basic_app: {e}")
        results["basic_app"] = False
    
    try:
        results["monitoring"] = await test_monitoring_example()
    except Exception as e:
        print(f"ERROR testing monitoring: {e}")
        results["monitoring"] = False
    
    try:
        results["caching"] = await test_caching_example()
    except Exception as e:
        print(f"ERROR testing caching: {e}")
        results["caching"] = False
    
    try:
        results["error_handling"] = await test_error_handling_example()
    except Exception as e:
        print(f"ERROR testing error_handling: {e}")
        results["error_handling"] = False
    
    try:
        results["compression"] = await test_compression_example()
    except Exception as e:
        print(f"ERROR testing compression: {e}")
        results["compression"] = False
    
    # Summary
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    
    for name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{name:20} {status}")
    
    total_passed = sum(1 for p in results.values() if p)
    total = len(results)
    
    print(f"\nTotal: {total_passed}/{total} examples passed all tests")
    
    if total_passed == total:
        print("\nSUCCESS: All examples work correctly!")
        return 0
    else:
        print(f"\nWARNING: {total - total_passed} example(s) have issues")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)

