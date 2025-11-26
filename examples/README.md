# QakeAPI 1.2.0 Application Examples

## Basic Examples

### `basic_example.py`
Simple example demonstrating core features:
- Hybrid sync/async support
- Smart routing
- Reactive events
- Query parameters
- Lifecycle events

**Run:**
```bash
py examples/basic_example.py
```

## Complete Examples

### `complete_example.py`
Complete example with all framework features:
- Hybrid sync/async
- Automatic parameter extraction from body
- Middleware system
- WebSocket support
- Background tasks
- Reactive events
- OpenAPI documentation

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

### Performance Optimization
- Caching of calculation results
- Background tasks for heavy operations
- Asynchronous processing

### Advanced Features
- WebSocket for real-time updates
- History of all calculations
- Statistics and analytics
- Automatic report generation

This is a full-featured web application demonstrating all capabilities of QakeAPI 1.2.0!
