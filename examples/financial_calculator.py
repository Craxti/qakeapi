"""
Financial Calculator - Mini-application on QakeAPI 1.2.0

This is a full-featured web application with:
- Complex financial calculations
- Background tasks for report generation
- WebSocket for real-time updates
- Middleware for logging and authentication
- Reactive events
- Result caching
"""

from qakeapi import QakeAPI, CORSMiddleware, LoggingMiddleware
from qakeapi.core.background import add_background_task
from qakeapi.core.websocket import WebSocket
import math
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional


app = QakeAPI(
    title="Financial Calculator API",
    version="1.2.0",
    description="Comprehensive web application for financial calculations",
    debug=True,
)

# Middleware
app.add_middleware(CORSMiddleware(allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]))
app.add_middleware(LoggingMiddleware())

# Cache for calculation results
calculation_cache: Dict[str, Dict] = {}
calculation_history: List[Dict] = []


# ========== HELPER FUNCTIONS FOR CALCULATIONS ==========

def calculate_compound_interest(principal: float, rate: float, time: float, n: int = 12) -> float:
    """
    Calculate compound interest.
    
    Formula: A = P(1 + r/n)^(nt)
    """
    return principal * (1 + rate / (n * 100)) ** (n * time)


def calculate_loan_payment(principal: float, rate: float, months: int) -> Dict[str, float]:
    """
    Calculate annuity loan payment.
    
    Formula: PMT = P * (r(1+r)^n) / ((1+r)^n - 1)
    """
    monthly_rate = rate / 12 / 100
    if monthly_rate == 0:
        payment = principal / months
    else:
        payment = principal * (monthly_rate * (1 + monthly_rate) ** months) / \
                  ((1 + monthly_rate) ** months - 1)
    
    total_paid = payment * months
    total_interest = total_paid - principal
    
    return {
        "monthly_payment": round(payment, 2),
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "interest_percentage": round((total_interest / principal) * 100, 2)
    }


def calculate_pension(salary: float, years: int, contribution_rate: float = 22) -> Dict[str, float]:
    """
    Calculate future pension.
    
    Calculates estimated pension based on current salary,
    years of service and contribution rate.
    """
    monthly_contribution = salary * (contribution_rate / 100)
    annual_contribution = monthly_contribution * 12
    
    # Expected return on pension savings (6% annually)
    expected_return = 0.06
    
    # Calculate accumulated savings with compound interest
    total_accumulated = 0
    for year in range(1, years + 1):
        total_accumulated = (total_accumulated + annual_contribution) * (1 + expected_return)
    
    # Calculate monthly pension (divide savings by expected payout period - 20 years)
    pension_months = 20 * 12
    monthly_pension = total_accumulated / pension_months if pension_months > 0 else 0
    
    # Calculate replacement rate
    replacement_rate = (monthly_pension / salary) * 100
    
    return {
        "total_accumulated": round(total_accumulated, 2),
        "monthly_pension": round(monthly_pension, 2),
        "replacement_rate": round(replacement_rate, 2),
        "total_contributed": round(annual_contribution * years, 2),
        "investment_growth": round(total_accumulated - (annual_contribution * years), 2)
    }


def calculate_investment_portfolio(
    initial_investment: float,
    monthly_contribution: float,
    years: int,
    expected_return: float = 7.0,
    inflation: float = 3.0
) -> Dict[str, any]:
    """
    Calculate investment portfolio with inflation adjustment.
    """
    real_return = (expected_return - inflation) / 100
    monthly_return = (1 + expected_return / 100) ** (1 / 12) - 1
    
    # Calculate future value
    future_value = initial_investment
    contributions_total = initial_investment
    
    monthly_values = []
    for month in range(1, years * 12 + 1):
        future_value = future_value * (1 + monthly_return) + monthly_contribution
        contributions_total += monthly_contribution
        
        if month % 12 == 0:
            year = month // 12
            # Adjusted for inflation
            real_value = future_value / ((1 + inflation / 100) ** year)
            monthly_values.append({
                "year": year,
                "nominal_value": round(future_value, 2),
                "real_value": round(real_value, 2),
                "contributions": round(contributions_total, 2),
                "growth": round(future_value - contributions_total, 2)
            })
    
    # Final values
    final_nominal = future_value
    final_real = future_value / ((1 + inflation / 100) ** years)
    total_growth = final_nominal - contributions_total
    growth_percentage = (total_growth / contributions_total) * 100 if contributions_total > 0 else 0
    
    return {
        "initial_investment": initial_investment,
        "monthly_contribution": monthly_contribution,
        "years": years,
        "final_nominal_value": round(final_nominal, 2),
        "final_real_value": round(final_real, 2),
        "total_contributions": round(contributions_total, 2),
        "total_growth": round(total_growth, 2),
        "growth_percentage": round(growth_percentage, 2),
        "yearly_breakdown": monthly_values
    }


# ========== API ENDPOINTS ==========

@app.get("/")
def root():
    """Main page with API description."""
    return {
        "name": "Financial Calculator API",
        "version": "1.2.0",
        "endpoints": {
            "loans": "/loans/calculate - Loan calculation",
            "investments": "/investments/calculate - Investment calculation",
            "pension": "/pension/calculate - Pension calculation",
            "compound_interest": "/interest/compound - Compound interest",
            "reports": "/reports/generate - Report generation",
            "statistics": "/statistics - Calculation statistics",
            "history": "/history - Calculation history",
            "cache": "/cache/stats - Cache statistics"
        },
        "websocket": "/ws/calculations - WebSocket for updates"
    }


@app.post("/loans/calculate")
async def calculate_loan(request):
    """Loan calculation with detailed information."""
    data = await request.json()
    
    principal = float(data.get("principal", 1000000))
    rate = float(data.get("rate", 10.0))
    months = int(data.get("months", 60))
    
    # Validation
    if principal <= 0 or rate < 0 or months <= 0:
        return {"error": "Invalid parameters"}, 400
    
    # Create cache key
    cache_key = f"loan_{principal}_{rate}_{months}"
    
    # Check cache
    if cache_key in calculation_cache:
        result = calculation_cache[cache_key].copy()
        result["cached"] = True
        return result
    
    # Perform calculation
    result = calculate_loan_payment(principal, rate, months)
    
    # Detailed payment schedule
    monthly_rate = rate / 12 / 100
    remaining_principal = principal
    payment_schedule = []
    
    monthly_payment = result["monthly_payment"]
    
    for month in range(1, months + 1):
        interest_payment = remaining_principal * monthly_rate
        principal_payment = monthly_payment - interest_payment
        remaining_principal -= principal_payment
        
        payment_schedule.append({
            "month": month,
            "payment": round(monthly_payment, 2),
            "interest": round(interest_payment, 2),
            "principal": round(principal_payment, 2),
            "remaining": round(max(0, remaining_principal), 2)
        })
    
    result["payment_schedule"] = payment_schedule
    result["cached"] = False
    
    # Save to cache and history
    calculation_cache[cache_key] = result.copy()
    calculation_history.append({
        "type": "loan",
        "timestamp": datetime.now().isoformat(),
        "params": {"principal": principal, "rate": rate, "months": months},
        "result": result
    })
    
    # Emit event
    await app.emit("calculation:completed", {
        "type": "loan",
        "params": {"principal": principal, "rate": rate, "months": months}
    })
    
    return result


@app.post("/investments/calculate")
async def calculate_investment(request):
    """Investment portfolio calculation."""
    data = await request.json()
    
    initial = float(data.get("initial_investment", 100000))
    monthly = float(data.get("monthly_contribution", 10000))
    years = int(data.get("years", 10))
    expected_return = float(data.get("expected_return", 7.0))
    inflation = float(data.get("inflation", 3.0))
    
    if initial < 0 or monthly < 0 or years <= 0:
        return {"error": "Invalid parameters"}, 400
    
    # Cache key
    cache_key = f"investment_{initial}_{monthly}_{years}_{expected_return}_{inflation}"
    
    if cache_key in calculation_cache:
        result = calculation_cache[cache_key].copy()
        result["cached"] = True
        return result
    
    # Calculation (this may take time)
    result = calculate_investment_portfolio(initial, monthly, years, expected_return, inflation)
    result["cached"] = False
    
    # Save
    calculation_cache[cache_key] = result.copy()
    calculation_history.append({
        "type": "investment",
        "timestamp": datetime.now().isoformat(),
        "params": {
            "initial": initial,
            "monthly": monthly,
            "years": years,
            "return": expected_return,
            "inflation": inflation
        },
        "result": result
    })
    
    # Background task for report generation
    await add_background_task(
        generate_investment_report,
        result,
        years
    )
    
    await app.emit("calculation:completed", {
        "type": "investment",
        "params": {"initial": initial, "monthly": monthly, "years": years}
    })
    
    return result


@app.post("/pension/calculate")
async def calculate_pension_endpoint(request):
    """Future pension calculation."""
    data = await request.json()
    
    salary = float(data.get("salary", 100000))
    years = int(data.get("years", 30))
    contribution_rate = float(data.get("contribution_rate", 22.0))
    
    if salary <= 0 or years <= 0:
        return {"error": "Invalid parameters"}, 400
    
    cache_key = f"pension_{salary}_{years}_{contribution_rate}"
    
    if cache_key in calculation_cache:
        result = calculation_cache[cache_key].copy()
        result["cached"] = True
        return result
    
    result = calculate_pension(salary, years, contribution_rate)
    result["cached"] = False
    
    calculation_cache[cache_key] = result.copy()
    calculation_history.append({
        "type": "pension",
        "timestamp": datetime.now().isoformat(),
        "params": {"salary": salary, "years": years, "rate": contribution_rate},
        "result": result
    })
    
    await app.emit("calculation:completed", {
        "type": "pension",
        "params": {"salary": salary, "years": years}
    })
    
    return result


@app.post("/interest/compound")
def calculate_compound_interest_endpoint(
    principal: float,
    rate: float,
    time: float,
    n: int = 12
):
    """Compound interest calculation (synchronous function)."""
    if principal <= 0 or rate < 0 or time <= 0:
        return {"error": "Invalid parameters"}, 400
    
    result = calculate_compound_interest(principal, rate, time, n)
    interest = result - principal
    
    return {
        "principal": principal,
        "rate": rate,
        "time": time,
        "compounding_frequency": n,
        "final_amount": round(result, 2),
        "interest_earned": round(interest, 2),
        "interest_percentage": round((interest / principal) * 100, 2)
    }


@app.get("/statistics")
def get_statistics():
    """Statistics for all calculations."""
    if not calculation_history:
        return {
            "total_calculations": 0,
            "cache_size": len(calculation_cache),
            "by_type": {}
        }
    
    by_type = {}
    for calc in calculation_history:
        calc_type = calc["type"]
        by_type[calc_type] = by_type.get(calc_type, 0) + 1
    
    return {
        "total_calculations": len(calculation_history),
        "cache_size": len(calculation_cache),
        "by_type": by_type,
        "latest_calculation": calculation_history[-1]["timestamp"] if calculation_history else None
    }


@app.get("/history")
def get_history(limit: int = 10):
    """Calculation history."""
    return {
        "total": len(calculation_history),
        "calculations": calculation_history[-limit:]
    }


@app.get("/cache/stats")
def get_cache_stats():
    """Cache statistics."""
    return {
        "size": len(calculation_cache),
        "keys": list(calculation_cache.keys())[:10]  # First 10 keys
    }


@app.delete("/cache/clear")
def clear_cache():
    """Clear cache."""
    global calculation_cache
    cleared_count = len(calculation_cache)
    calculation_cache.clear()
    return {
        "message": "Cache cleared",
        "cleared_count": cleared_count
    }


@app.post("/reports/generate")
async def generate_report(request):
    """Report generation in background mode."""
    data = await request.json()
    report_type = data.get("type", "summary")
    
    # Start background task
    task_id = await add_background_task(
        generate_comprehensive_report,
        report_type,
        calculation_history
    )
    
    return {
        "message": "Report generation started",
        "task_id": task_id,
        "type": report_type
    }


# ========== BACKGROUND TASKS ==========

async def generate_investment_report(result: Dict, years: int):
    """Generate detailed investment report."""
    print(f"[Background Task] Generating investment report for {years} years...")
    
    # Simulate long calculation
    await asyncio.sleep(2)
    
    report = {
        "type": "investment_report",
        "generated_at": datetime.now().isoformat(),
        "years": years,
        "summary": {
            "final_value": result.get("final_nominal_value"),
            "total_contributions": result.get("total_contributions"),
            "growth": result.get("total_growth")
        }
    }
    
    print(f"[Background Task] Report generated: {report}")
    return report


async def generate_comprehensive_report(report_type: str, history: List[Dict]):
    """Generate comprehensive report."""
    print(f"[Background Task] Generating comprehensive report of type: {report_type}")
    
    await asyncio.sleep(3)  # Simulate processing
    
    report = {
        "type": report_type,
        "generated_at": datetime.now().isoformat(),
        "total_calculations": len(history),
        "summary": {
            "loans": sum(1 for h in history if h["type"] == "loan"),
            "investments": sum(1 for h in history if h["type"] == "investment"),
            "pensions": sum(1 for h in history if h["type"] == "pension")
        }
    }
    
    print(f"[Background Task] Comprehensive report ready: {report}")
    return report


# ========== REACTIVE EVENTS ==========

@app.react("calculation:completed")
async def on_calculation_completed(event):
    """Handler for calculation completion event."""
    calc_type = event.data.get("type")
    print(f"[Event] Calculation completed: {calc_type}")
    
    # Can send notification, save to DB, etc.


# ========== WEBSOCKET ==========

@app.websocket("/ws/calculations")
async def calculations_websocket(websocket: WebSocket):
    """WebSocket for real-time calculation updates."""
    await websocket.accept()
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to financial calculator",
            "timestamp": datetime.now().isoformat()
        })
        
        # Simulate updates
        counter = 0
        while True:
            await asyncio.sleep(5)  # Updates every 5 seconds
            
            counter += 1
            await websocket.send_json({
                "type": "update",
                "counter": counter,
                "statistics": {
                    "total_calculations": len(calculation_history),
                    "cache_size": len(calculation_cache)
                },
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


# ========== LIFECYCLE ==========

@app.on_startup
def startup():
    """Initialization on startup."""
    print("=" * 60)
    print("Financial Calculator started!")
    print("=" * 60)
    print("\nAvailable endpoints:")
    print("  POST /loans/calculate - Loan calculation")
    print("  POST /investments/calculate - Investment calculation")
    print("  POST /pension/calculate - Pension calculation")
    print("  POST /interest/compound - Compound interest")
    print("  GET  /statistics - Statistics")
    print("  GET  /history - Calculation history")
    print("  WS   /ws/calculations - WebSocket updates")
    print("=" * 60)


@app.on_shutdown
def shutdown():
    """Cleanup on shutdown."""
    print("\nFinancial Calculator shutting down...")


if __name__ == "__main__":
    import uvicorn
    import asyncio
    import sys
    import io
    
    # Fix encoding for Windows console
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("\nStarting financial calculator...\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

