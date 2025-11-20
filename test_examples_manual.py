"""
Manual test script - run examples one by one and test endpoints
This is simpler and more reliable than automated testing
"""
import sys
import subprocess
import time
import os

def test_example(example_name, port, endpoints):
    """Test a single example"""
    print(f"\n{'='*60}")
    print(f"Testing: {example_name}")
    print(f"{'='*60}")
    
    # Start server
    process = subprocess.Popen(
        [sys.executable, f"examples/{example_name}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, 'PYTHONPATH': os.getcwd()},
    )
    
    print(f"Server starting on port {port}...")
    print("Wait a few seconds, then test endpoints manually:")
    print(f"\nExample commands:")
    for method, path, desc in endpoints:
        if method == "GET":
            print(f"  curl http://localhost:{port}{path}")
        elif method == "POST":
            print(f"  curl -X POST http://localhost:{port}{path} -H 'Content-Type: application/json' -d '{{\"name\":\"test\"}}'")
    
    print(f"\nPress Enter when done testing...")
    input()
    
    process.terminate()
    process.wait()
    print("Server stopped.\n")

def main():
    examples = [
        ("basic_app.py", 8000, [
            ("GET", "/", "Root"),
            ("GET", "/hello/World", "Hello"),
            ("GET", "/items/1?q=test", "Get item"),
            ("POST", "/items/", "Create item"),
        ]),
        ("monitoring_example.py", 8001, [
            ("GET", "/", "Root"),
            ("GET", "/metrics", "Metrics"),
            ("GET", "/health", "Health check"),
        ]),
        ("caching_example.py", 8002, [
            ("GET", "/", "Root"),
            ("GET", "/items/2", "Get item 2"),
            ("GET", "/items/", "Get all items"),
            ("GET", "/cache/stats", "Cache stats"),
        ]),
        ("error_handling_example.py", 8004, [
            ("GET", "/", "Root"),
            ("GET", "/success", "Success"),
            ("GET", "/not-found", "404 error"),
            ("GET", "/validation-error", "Validation error"),
        ]),
        ("compression_example.py", 8005, [
            ("GET", "/", "Root"),
            ("GET", "/small", "Small response"),
            ("GET", "/large", "Large response"),
        ]),
    ]
    
    print("="*60)
    print("Manual Testing of QakeAPI Examples")
    print("="*60)
    print("\nThis script will start each example server.")
    print("You can then test endpoints manually using curl or a browser.")
    print("\nPress Enter to start...")
    input()
    
    for example_name, port, endpoints in examples:
        test_example(example_name, port, endpoints)
    
    print("\n" + "="*60)
    print("All examples tested!")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)

