# Changelog

All notable changes to QakeAPI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2026-01-xx

### Changed
- Version bump 1.3.0 → 1.3.1

## [1.3.0] - 2026-01-xx

### Added
- **Community & Ecosystem** — docs/COMMUNITY.md, docs/ecosystem.md (integrations: SQLite, Redis, Docker, Celery)
- **Trust & Discoverability** — "Used by" section, PyPI keywords, .github/FUNDING.yml, docs/DISCOVERABILITY.md
- **Documentation** — docs/tutorial.md (step-by-step), mkdocs.yml (docs site), README_RU.md (Russian)
- **Developer Experience** — .pre-commit-config.yaml, .vscode/qakeapi.code-snippets
- docs/index.md for MkDocs
- docs extras in setup.py (mkdocs, mkdocs-material)

### Changed
- Version bump 1.2.0 → 1.3.0

## [1.2.0] - 2026-01-xx

### Added
- Hybrid sync/async execution with automatic conversion
- Reactive event system with `emit` and `react`
- Parallel dependency resolution
- Pipeline composition for function chaining
- Smart conditional routing with `@app.when`
- Trie-based router for optimized path matching
- OpenAPI/Swagger automatic documentation
- WebSocket support
- Background tasks
- Middleware system (CORS, Logging, RequestSizeLimit)
- Dependency injection with `Depends`
- Rate limiting decorator
- Response caching with TTL
- Request validation
- File upload with type and size validation
- JWT and session authentication
- Comprehensive documentation in Markdown
- Financial calculator example application

### Changed
- Documentation migrated from RST to Markdown
- Project structure simplified
- Examples reorganized into `examples/` directory

### Fixed
- Removed broken CLI entry point from setup.py

## [1.1.2] - 2024-xx-xx

### Added
- Additional features and improvements

## [1.1.1] - 2024-xx-xx

### Added
- Initial release features

## [1.0.0] - 2024-xx-xx

### Added
- Initial release of QakeAPI
