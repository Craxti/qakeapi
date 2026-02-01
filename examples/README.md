# QakeAPI 1.2.0 Application Examples

Each example demonstrates **why QakeAPI is better** — zero deps, hybrid sync/async, built-in features that other frameworks require extra packages for.

## Basic Examples

### `basic_example.py`
Simple example demonstrating core features. **Why QakeAPI:**
- **Hybrid sync/async** — `get_user` is sync, `get_item` is async; both work without manual wrapping. ~15K RPS for sync vs Flask ~3K.
- **Smart routing** — `@app.when()` for conditional routes (mobile, v2 API). Trie-based lookup for static paths.
- **Reactive events** — `emit`/`react` built-in; no Celery or Redis for simple event-driven flows.
- **Query params** — Automatic extraction and validation from type hints.
- **Lifecycle events** — `on_startup`/`on_shutdown` without extra middleware.

**Run:**
```bash
py examples/basic_example.py
```

## Complete Examples

### `complete_example.py`
Complete example with all framework features. **Why QakeAPI:**
- **Hybrid sync/async** — Mix sync and async handlers freely; no `run_in_executor` boilerplate.
- **Parameter extraction** — Body/query/path params from type hints; no Pydantic required.
- **Middleware** — CORS, Logging, RequestSizeLimit built-in; no `starlette.middleware` imports.
- **WebSocket** — Native ASGI; `iter_json()` helper; ~1.2K connections/sec vs Flask-SocketIO ~450.
- **Background tasks** — `add_background_task()`; no Celery/Redis for fire-and-forget jobs.
- **Reactive events** — Event bus in core; decouple handlers without message queues.
- **OpenAPI** — Auto-generated docs at `/docs`; same UX as FastAPI, zero extra deps.

**Run:**
```bash
py examples/complete_example.py
```

### `financial_calculator.py` 🆕
**Full-featured Web Application - Financial Calculator**

Comprehensive mini-application with real calculations:

#### Features:
- 📊 **Loan Calculations** - annuity payments, payment schedule
- 💰 **Investment Calculations** - portfolio with inflation, compound interest
- 🏦 **Pension Calculations** - future pension, replacement rate
- 📈 **Compound Interest** - savings calculation
- 📝 **Report Generation** - background tasks for report creation
- 📊 **Statistics** - analysis of all calculations
- 🔄 **WebSocket** - real-time updates
- 💾 **Caching** - optimization of repeated calculations
- 📚 **Calculation History** - saving all operations

#### API Endpoints:

**Loans:**
```bash
POST /loans/calculate
Body: {
  "principal": 1000000,  # Loan amount
  "rate": 10.0,          # Annual interest rate
  "months": 60           # Term in months
}
```

**Investments:**
```bash
POST /investments/calculate
Body: {
  "initial_investment": 100000,     # Initial investment
  "monthly_contribution": 10000,    # Monthly contribution
  "years": 10,                      # Investment period
  "expected_return": 7.0,           # Expected return %
  "inflation": 3.0                  # Inflation %
}
```

**Pension:**
```bash
POST /pension/calculate
Body: {
  "salary": 100000,       # Current salary
  "years": 30,            # Years of service
  "contribution_rate": 22 # Contribution rate
}
```

**Compound Interest:**
```bash
POST /interest/compound?principal=100000&rate=7.0&time=10&n=12
```

**Other endpoints:**
- `GET /statistics` - Statistics of all calculations
- `GET /history?limit=10` - Calculation history
- `GET /cache/stats` - Cache statistics
- `DELETE /cache/clear` - Clear cache
- `POST /reports/generate` - Report generation (background task)
- `WS /ws/calculations` - WebSocket for updates

**Run:**
```bash
py examples/financial_calculator.py
```

**Documentation:**
- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

## Financial Calculator Features

### Real Calculations
- Uses real financial formulas
- Accounts for inflation and compound interest
- Detailed payment schedules

### Performance Optimization — Why QakeAPI Wins
- **Caching** — `@cache(ttl=300)` on expensive endpoints; cache hits ~42K RPS vs compute ~16K. No Redis needed.
- **Background tasks** — Report generation runs in background; response returns immediately. No Celery.
- **Async processing** — Loan/investment calculations don't block the event loop; more concurrent users.

### Advanced Features
- **WebSocket** — Real-time updates to connected clients; native ASGI, no extra protocol layer.
- **History & stats** — In-memory storage; for production add DB via `Depends(get_db)`.
- **OpenAPI** — Full docs at `/docs`; clients can generate SDKs automatically.

This is a full-featured web application demonstrating all capabilities of QakeAPI 1.2.0! See [benchmarks](../docs/benchmarks.md) for performance numbers.
