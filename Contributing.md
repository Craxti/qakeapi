# Contributing to QakeAPI

First off, thanks for taking the time to contribute! 🎉👍

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Pull Requests](#pull-requests)
- [Development Setup](#development-setup)
- [Styleguides](#styleguides)
  - [Git Commit Messages](#git-commit-messages)
  - [Python Styleguide](#python-styleguide)
  - [Documentation Styleguide](#documentation-styleguide)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots if possible

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Include screenshots and animated GIFs in your pull request whenever possible
* Follow the Python styleguide
* Include tests
* Document new code
* End all files with a newline

## Development Setup

1. Fork the repo
2. Clone your fork
```bash
git clone https://github.com/your-username/qakeapi.git
cd qakeapi
```

3. Create a virtual environment and activate it
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install development dependencies
```bash
pip install -e ".[dev]"
```

5. Create a branch for your changes
```bash
git checkout -b feature-or-fix-name
```

6. Make your changes and run tests
```bash
pytest
```

## Styleguides

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line
* Consider starting the commit message with an applicable emoji:
    * 🎨 `:art:` when improving the format/structure of the code
    * 🐎 `:racehorse:` when improving performance
    * 🚱 `:non-potable_water:` when plugging memory leaks
    * 📝 `:memo:` when writing docs
    * 🐛 `:bug:` when fixing a bug
    * 🔥 `:fire:` when removing code or files
    * 💚 `:green_heart:` when fixing the CI build
    * ✅ `:white_check_mark:` when adding tests
    * 🔒 `:lock:` when dealing with security
    * ⬆️ `:arrow_up:` when upgrading dependencies
    * ⬇️ `:arrow_down:` when downgrading dependencies

### Python Styleguide

* Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
* Use [Black](https://github.com/psf/black) for code formatting
* Use [isort](https://pycqa.github.io/isort/) for import sorting
* Use type hints whenever possible
* Write docstrings for all public methods and classes

### Documentation Styleguide

* Use [Markdown](https://guides.github.com/features/mastering-markdown/) for documentation
* Reference functions and classes with backticks: \`myfunction()\`
* Include code examples when possible
* Keep line length to 80 characters or less
* Include a table of contents for long documents

## Additional Notes

### Issue and Pull Request Labels

| Label name | Description |
| --- | --- |
| `bug` | Confirmed bugs or reports that are very likely to be bugs |
| `enhancement` | Feature requests |
| `documentation` | Documentation improvements |
| `good first issue` | Good for newcomers |
| `help wanted` | Extra attention is needed |
| `question` | Questions more than bug reports or feature requests |

---

Thank you for contributing to QakeAPI! 🚀 