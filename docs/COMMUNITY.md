# QakeAPI Community & Ecosystem

## Get Involved

### GitHub Discussions

Ask questions, share ideas, and discuss QakeAPI:

**[→ GitHub Discussions](https://github.com/craxti/qakeapi/discussions)**

- **Q&A** — Get help from maintainers and community
- **Ideas** — Suggest new features
- **Show and tell** — Share your projects built with QakeAPI
- **General** — Off-topic discussions

*Enable Discussions in your repo: Settings → General → Features → Discussions*

### Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to contribute code, docs, or examples.

### Report Issues

- **Bugs:** [Bug report template](https://github.com/craxti/qakeapi/issues/new?template=bug_report.md)
- **Features:** [Feature request template](https://github.com/craxti/qakeapi/issues/new?template=feature_request.md)

---

## Ecosystem

### Official Examples

| Example | Description |
|---------|-------------|
| [basic_example](../examples/basic_example.py) | Hybrid sync/async, routing, events |
| [complete_example](../examples/complete_example.py) | Full feature showcase |
| [financial_calculator](../examples/financial_calculator.py) | Real-world app with caching, WebSocket |
| [auth_example](../examples/auth_example.py) | JWT authentication |
| [file_upload_example](../examples/file_upload_example.py) | File upload with validation |
| [caching_example](../examples/caching_example.py) | Response caching |
| [rate_limit_example](../examples/rate_limit_example.py) | Rate limiting |

### Integrations

QakeAPI works with popular Python libraries. Example patterns:

| Library | Use case | Example |
|---------|----------|---------|
| **SQLite** | Lightweight DB | `Depends(get_db)` with `sqlite3` |
| **SQLAlchemy** | ORM | `Depends(get_session)` |
| **Redis** | Caching, sessions | Custom cache backend |
| **httpx** | HTTP client | Async API calls in handlers |
| **uvicorn** | ASGI server | `uvicorn.run(app)` |

### Awesome QakeAPI

Curated list of resources:

- [Documentation](https://github.com/craxti/qakeapi/tree/main/docs)
- [Examples](https://github.com/craxti/qakeapi/tree/main/examples)
- [Benchmarks](benchmarks.md)
- [Migration from FastAPI](migration-from-fastapi.md)

*Add your project: open a PR or Discussion!*

---

## Support the Project

- **Star** the repo on GitHub
- **Share** QakeAPI with your network
- **Contribute** code, docs, or examples
- **Sponsor** — [GitHub Sponsors](https://github.com/sponsors/craxti) (when available)
