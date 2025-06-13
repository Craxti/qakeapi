# Contributing to QakeAPI

Thank you for your interest in contributing to QakeAPI! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please read it before contributing.

## How to Contribute

### 1. Fork the Repository

1. Go to [QakeAPI on GitHub](https://github.com/Craxti/qakeapi)
2. Click the "Fork" button in the top-right corner
3. Clone your fork:
```bash
git clone https://github.com/craxti/qakeapi.git
cd qakeapi
```

### 2. Set Up Development Environment

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install development dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Create a Branch

Create a new branch for your feature or bugfix:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bugfix-name
```

### 4. Make Changes

1. Write your code
2. Add tests for your changes
3. Run the test suite:
```bash
pytest
```

4. Check code style:
```bash
flake8
black .
isort .
```

### 5. Commit Your Changes

Follow our commit message format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

Example:
```
feat(auth): add JWT authentication support

- Add JWT token generation
- Add token validation middleware
- Add refresh token endpoint

Closes #123
```

### 6. Push and Create Pull Request

1. Push your changes:
```bash
git push origin feature/your-feature-name
```

2. Create a Pull Request on GitHub
3. Fill out the PR template
4. Wait for review

## Development Guidelines

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public functions
- Keep functions small and focused
- Write meaningful variable names

### Testing

- Write unit tests for new features
- Maintain test coverage
- Test edge cases
- Use pytest fixtures

### Documentation

- Update README.md if needed
- Add docstrings to new functions
- Update API documentation
- Add examples for new features

## Review Process

1. All PRs require at least one review
2. CI must pass
3. Code coverage must not decrease
4. Documentation must be updated
5. Tests must be added

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag
4. Build and publish to PyPI

## Need Help?

- Open an issue
- Join our [Discussions](https://github.com/Craxti/qakeapi/discussions)
- Check the [FAQ](FAQ)

## License

By contributing to QakeAPI, you agree that your contributions will be licensed under the project's MIT License. 