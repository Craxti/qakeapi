from qakeapi.core.application import Application
from qakeapi.security.rate_limit import InMemoryRateLimiter, RateLimitMiddleware
from qakeapi.core.responses import Response

# Создаем приложение
app = Application()

# Настраиваем rate limiting: 5 запросов в минуту
rate_limiter = InMemoryRateLimiter(requests_per_minute=5)

# Отдельный rate limiter для защищенных эндпоинтов
api_rate_limiter = InMemoryRateLimiter(requests_per_minute=2)

@app.router.middleware()
async def rate_limit_middleware(request, handler):
    """Rate limit middleware implementation"""
    key = request.client.host
    
    # Выбираем подходящий rate limiter
    if request.path.startswith("/protected"):
        limiter = api_rate_limiter
    else:
        limiter = rate_limiter
        
    # Проверяем лимит
    if not await limiter.check_rate_limit(key):
        return Response.json(
            {"detail": "Rate limit exceeded"}, 
            status_code=429
        )
        
    return await handler(request)

@app.router.route("/", methods=["GET"])
async def index(request):
    return Response.json({"message": "Hello from Rate Limited API!"})

@app.router.route("/api", methods=["GET"])
async def api(request):
    return Response.json({"data": "API response"})

@app.router.route("/protected", methods=["GET"])
async def protected(request):
    return Response.json({"data": "Protected API response"})

if __name__ == "__main__":
    import uvicorn
    from config import PORTS
    uvicorn.run(app, host="127.0.0.1", port=PORTS['rate_limit_app']) 