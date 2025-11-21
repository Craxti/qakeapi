# Release v1.1.2

## 🐛 Bug Fixes
- Fixed RateLimiter event loop initialization issue
- Fixed cache middleware x-cache header handling
- Fixed async fixture handling in integration tests

## ✨ Improvements
- Enhanced JWT authentication support with proper error handling
- Improved caching with HIT/MISS headers
- Added comprehensive dependency management (PyJWT, cryptography, jinja2, watchdog, aiohttp)
- Code formatting with black
- Import sorting with isort

## 📚 Documentation
- Configured GitHub Pages for automatic documentation deployment
- Added setup instructions for GitHub Pages

## 🧪 Testing
- Fixed 35+ test errors related to dependencies
- Improved test coverage to 54%
- Added demo testing scripts

## 📦 Dependencies
- Added all optional dependencies to `pyproject.toml` and `requirements-dev.txt`
- Ensured all tests can run with proper dependencies installed

---

**Full Changelog**: See commit history for detailed changes.

