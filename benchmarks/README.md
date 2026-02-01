# QakeAPI Benchmarks

Run benchmarks to measure QakeAPI performance and compare with other frameworks.

## Prerequisites

```bash
pip install qakeapi uvicorn httpx
```

## Quick Run

```bash
# From project root — starts server, runs benchmarks, prints results
python benchmarks/run_benchmarks.py
```

## Manual Run

1. Start the server:
   ```bash
   uvicorn examples.basic_example:app --host 127.0.0.1 --port 8000
   ```

2. Run wrk (install: `brew install wrk` or `apt install wrk`):
   ```bash
   wrk -t4 -c100 -d30s http://127.0.0.1:8000/
   ```

3. Or use the Python script (with server already running):
   ```bash
   # Edit run_benchmarks.py to skip server startup, then:
   python benchmarks/run_benchmarks.py
   ```

## Expected Results

See [docs/benchmarks.md](../docs/benchmarks.md) for detailed numbers and explanations of why QakeAPI performs better in each scenario.

Typical numbers (Apple M1 / Intel i7, Python 3.11):
- Simple JSON: ~18K RPS
- Path params: ~17K RPS
- With 2 middleware: ~15K RPS
