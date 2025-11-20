# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of QakeAPI framework
- Core HTTP server with routing
- WebSocket support
- Middleware system (CORS, Auth, Logging, Compression)
- Data validation with Pydantic
- Automatic OpenAPI documentation generation
- Dependency injection system
- Static files and template support
- Security features (JWT, password hashing, rate limiting)
- Monitoring and health checks
- Caching system (in-memory and Redis)
- CLI development tools
- Comprehensive test suite (201 tests)

### Changed
- Translated all code comments and docstrings to English
- Improved error handling and error messages
- Enhanced documentation

### Fixed
- Fixed middleware recursion issues
- Fixed Windows compatibility issues with cryptography
- Fixed import errors in example applications
- Fixed duplicate properties in Request class

## [1.1.0] - 2024-11-20

### Added
- Enhanced error handling with better exception prioritization
- Improved Windows compatibility for database tests
- Better MIME type detection across different operating systems
- Non-blocking black formatting check in CI

### Fixed
- Fixed Windows-specific test failures (database file locking, MIME type detection)
- Fixed code formatting issues across multiple files
- Fixed httpx compatibility issues in tests
- Fixed Response serialization in tests

### Changed
- Made black formatting check non-blocking in CI
- Updated Python version requirement to >=3.9

## [0.1.0] - 2024-01-XX

### Added
- Initial public release
- Basic HTTP server functionality
- Route registration and handling
- Request/Response objects
- Exception handling
- Basic middleware support

---

## Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

