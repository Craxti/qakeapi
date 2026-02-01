# Contributing to QakeAPI

Thank you for your interest in contributing to QakeAPI! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Git

### Clone the Repository

```bash
git clone https://github.com/craxti/qakeapi.git
cd qakeapi
```

### Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -e ".[dev,test,server]"
```

### Run Tests

```bash
pytest tests/ -v
```

With coverage:

```bash
pytest tests/ -v --cov=qakeapi --cov-report=term-missing
```

## Development Workflow

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes** following the code style guidelines below.

3. **Run tests** to ensure nothing is broken:
   ```bash
   pytest tests/ -v
   ```

4. **Commit your changes** with a clear message:
   ```bash
   git add .
   git commit -m "Add: description of your change"
   ```

5. **Push and create a Pull Request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- Use **Black** for code formatting:
  ```bash
  black qakeapi/ tests/ examples/
  ```

- Use **Flake8** for linting:
  ```bash
  flake8 qakeapi/ tests/
  ```

- Follow PEP 8 guidelines.
- Use type hints where appropriate.
- Write docstrings for public functions and classes.

## Pull Request Guidelines

- Keep PRs focused on a single feature or fix.
- Update documentation if you change public APIs.
- Add tests for new functionality.
- Ensure all tests pass before submitting.
- Use the PR template when creating a pull request.

## Commit Message Format

Use clear, descriptive commit messages:

- `Add: new feature description`
- `Fix: bug description`
- `Update: what was updated`
- `Docs: documentation changes`
- `Refactor: refactoring description`

## Reporting Bugs

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) when opening an issue. Include:

- QakeAPI version
- Python version
- Steps to reproduce
- Expected vs actual behavior
- Relevant code snippets

## Suggesting Features

Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md) when suggesting new features. Include:

- Clear description of the feature
- Use case / motivation
- Possible implementation approach
- Alternatives considered

## Questions?

Feel free to open a [Discussion](https://github.com/craxti/qakeapi/discussions) for questions, ideas, or general feedback.

Thank you for contributing! 🚀
