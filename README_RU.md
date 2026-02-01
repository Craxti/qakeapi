# 🚀 QakeAPI 1.3.1

**Революционный гибридный Async/Sync веб-фреймворк для Python**

QakeAPI — единственный Python веб-фреймворк с настоящим гибридным sync/async и **нулевыми зависимостями** в ядре. Пишите обычные функции — фреймворк автоматически превращает их в async.

## Установка

```bash
pip install qakeapi
```

## Быстрый старт

```python
from qakeapi import QakeAPI, CORSMiddleware

app = QakeAPI(title="Мой API", version="1.3.1")
app.add_middleware(CORSMiddleware(allow_origins=["*"]))

@app.get("/users/{id}")
def get_user(id: int):
    return {"id": id, "name": f"Пользователь {id}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Swagger UI: `http://localhost:8000/docs`

## Почему QakeAPI?

- **Нулевые зависимости** — только стандартная библиотека Python
- **Гибридный sync/async** — пишите обычные функции, они работают автоматически
- **OpenAPI/Swagger** — документация из коробки
- **WebSocket, DI, кэширование, rate limiting** — всё встроено
- **~18K RPS** vs ~3K у Flask — см. [benchmarks](docs/benchmarks.md)

## Документация

- [Getting Started](docs/getting-started.md)
- [Tutorial](docs/tutorial.md)
- [Benchmarks](docs/benchmarks.md)
- [Migration from FastAPI](docs/migration-from-fastapi.md)

## Лицензия

MIT — см. [LICENSE](LICENSE)
