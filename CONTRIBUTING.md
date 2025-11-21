# Contributing to QakeAPI

Thank you for your interest in contributing to QakeAPI! This document provides guidelines and instructions for contributing.

## Development Philosophy

QakeAPI is built with the following principles:

1. **All methods implemented independently** - We don't use external libraries for core functionality
2. **Python standard library only** - Core framework uses only built-in Python modules
3. **Clean and documented code** - All code should be well-documented and typed
4. **Comprehensive testing** - All components must have test coverage

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/craxti/qakeapi.git
   cd qakeapi
   ```
3. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the coding standards

3. Write or update tests for your changes

4. Run tests:
   ```bash
   pytest
   ```

5. Check code formatting:
   ```bash
   black qakeapi tests
   isort qakeapi tests
   ```

6. Check type hints:
   ```bash
   mypy qakeapi
   ```

7. Commit your changes:
   ```bash
   git commit -m "Add feature: description"
   ```

8. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

9. Open a Pull Request

## Coding Standards

### Code Style

- Follow PEP 8 style guide
- Use `black` for code formatting (line length: 88)
- Use `isort` for import sorting
- Use type hints everywhere
- Maximum line length: 88 characters

### Documentation

- All public functions and classes must have docstrings
- Use Google-style docstrings
- Document all parameters and return values
- Add comments for complex logic

### Testing

- Write tests for all new features
- Aim for >90% code coverage
- Use descriptive test names
- Test both success and failure cases

### Type Hints

- Use type hints for all function signatures
- Use `typing` module for complex types
- Use `Optional` for nullable values
- Use `Union` for multiple types

## Project Structure

```
qakeapi/
 core/           # Core framework components
 validation/     # Data validation
 security/       # Security features
 caching/        # Caching system
 monitoring/     # Metrics and health checks
 utils/          # Utility functions
 testing/        # Testing utilities

tests/              # Test suite
examples/           # Example applications
```

## Adding New Features

1. Check the [Development Plan](DEVELOPMENT_PLAN.md) to see if the feature is planned
2. Create an issue to discuss the feature (if not in the plan)
3. Implement the feature following the architecture
4. Write comprehensive tests
5. Update documentation
6. Submit a Pull Request

## Reporting Bugs

1. Check if the bug has already been reported
2. Create a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Python version
   - Environment details

## Code Review Process

1. All PRs require at least one approval
2. All tests must pass
3. Code must follow style guidelines
4. Documentation must be updated
5. No external dependencies for core functionality

## Questions?

Feel free to open an issue for questions or discussions about the project.

Thank you for contributing to QakeAPI!

