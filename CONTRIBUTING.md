# Contributing to QakeAPI

Thank you for your interest in contributing to QakeAPI! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list to see if the bug has already been reported. When creating a bug report, include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Environment details (Python version, OS, etc.)
- Code examples if applicable

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- A clear, descriptive title
- Detailed description of the proposed enhancement
- Use case and motivation
- Examples of how it would be used

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation if needed
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- pip

### Setup Steps

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/qakeapi.git
   cd qakeapi
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run tests to verify setup:**
   ```bash
   pytest tests/
   ```

## Coding Standards

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Maximum line length: 88 characters (Black default)

### Type Hints

- Use type hints for all function signatures
- Use `typing` module for complex types
- Run `mypy` to check type correctness

### Code Formatting

Before committing, run:
```bash
black qakeapi/ tests/ examples/
isort qakeapi/ tests/ examples/
```

### Docstrings

- Use Google-style docstrings
- Document all public functions, classes, and methods
- Include parameter descriptions and return types
- Add examples for complex functions

Example:
```python
def process_request(request: Request) -> Response:
    """
    Process an incoming HTTP request.
    
    Args:
        request: The HTTP request object
        
    Returns:
        The HTTP response object
        
    Raises:
        ValueError: If request is invalid
    """
    pass
```

## Testing

### Writing Tests

- Write tests for all new features
- Aim for high test coverage
- Use descriptive test names
- Follow the existing test structure

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_basic.py

# Run with coverage
pytest tests/ --cov=qakeapi --cov-report=html

# Run with verbose output
pytest tests/ -v
```

### Test Structure

Tests should be organized in the `tests/` directory mirroring the source structure:

```
tests/
├── test_basic.py
├── test_middleware.py
├── test_security.py
└── ...
```

## Submitting Changes

### Commit Messages

Write clear, descriptive commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and pull requests

Example:
```
Add rate limiting middleware

- Implement token bucket algorithm
- Add configuration options
- Include tests and documentation

Fixes #123
```

### Pull Request Process

1. **Update documentation** if your changes affect user-facing features
2. **Add tests** for new functionality
3. **Ensure all tests pass** and code is formatted
4. **Update CHANGELOG.md** with your changes
5. **Create a descriptive PR** with:
   - Clear title and description
   - Reference to related issues
   - Screenshots if applicable
   - Testing instructions

### Review Process

- All PRs require at least one approval
- Address review comments promptly
- Keep PRs focused and reasonably sized
- Rebase on main branch if needed

## Documentation

### Code Documentation

- Document all public APIs
- Include examples in docstrings
- Keep comments up-to-date with code

### User Documentation

- Update README.md for user-facing changes
- Add examples to QUICKSTART.md if needed
- Update API documentation if endpoints change

## Questions?

If you have questions about contributing, please:

- Open an issue with the `question` label
- Check existing issues and discussions
- Contact maintainers via email

Thank you for contributing to QakeAPI! 🚀

