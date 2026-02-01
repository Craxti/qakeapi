# Benchmark Results

QakeAPI benchmarks run automatically in CI on every push to `main`.

## View Latest Results

1. Go to [Actions → Benchmarks](https://github.com/craxti/qakeapi/actions/workflows/benchmarks.yml)
2. Click the latest workflow run
3. Scroll to **Artifacts** at the bottom
4. Download **benchmark-results** (contains `benchmark-results.txt` and `benchmark-results.md`)

Results are also visible in the **Job summary** of each run.

## Run Locally

```bash
pip install qakeapi uvicorn httpx
python benchmarks/run_benchmarks.py
```

## Environment

CI runs on `ubuntu-latest` with Python 3.11. Results may vary on different hardware.

## Detailed Benchmarks

For detailed numbers, comparisons with FastAPI/Flask, and explanations of why QakeAPI performs better, see [benchmarks.md](benchmarks.md).
