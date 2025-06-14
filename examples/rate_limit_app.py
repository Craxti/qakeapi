from qakeapi.core.application import Application
from qakeapi.security.rate_limit import InMemoryRateLimiter, RateLimitMiddleware
from qakeapi.core.responses import Response

# Создаем приложение
app = Application()

# Настраиваем rate limiting: 5 запросов в минуту
rate_limiter = InMemoryRateLimiter(requests_per_minute=5)
app.add_middleware(RateLimitMiddleware(rate_limiter))

@app.router.route("/", methods=["GET"])
async def index(request):
    return Response.json({"message": "Hello, World!"})

@app.router.route("/api", methods=["GET"])
async def api(request):
    return Response.json({"data": "API response"})

# Отдельный rate limiter для API endpoints с более строгими ограничениями
api_rate_limiter = InMemoryRateLimiter(requests_per_minute=2)
api_middleware = RateLimitMiddleware(
    api_rate_limiter,
    key_func=lambda request: request.headers.get("X-API-Key", "default")
)

# Добавляем middleware для защищенного эндпоинта
app.add_middleware(api_middleware)

@app.router.route("/protected", methods=["GET"])
async def protected(request):
    return Response.json({"data": "Protected API response"})

if __name__ == "__main__":
    import uvicorn
    from config import PORTS
    uvicorn.run(app, host="127.0.0.1", port=PORTS['rate_limit_app']) 