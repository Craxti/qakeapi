# QakeAPI

A modern, lightweight, and fast ASGI web framework for building APIs in Python.

[![Tests](https://github.com/Craxti/qakeapi/actions/workflows/tests.yml/badge.svg)](https://github.com/Craxti/qakeapi/actions/workflows/tests.yml)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 🌟 Features

- 🚀 High-performance ASGI framework
- 📝 Built-in OpenAPI/Swagger documentation
- 🔒 CORS middleware support
- 🔐 Authentication middleware
- 🎯 Type hints and modern Python features
- 📦 Easy to use and extend

## 📋 Categories

- #web-framework
- #api-framework
- #python
- #asgi
- #openapi
- #swagger
- #middleware
- #cors
- #authentication

## 🚀 Quick Start

```bash
pip install qakeapi
```

Basic example:

```python
from qakeapi import Application

app = Application()

@app.get("/")
async def hello():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    app.run()
```

## 📚 Documentation

Visit our [documentation](https://github.com/Craxti/qakeapi/wiki) for detailed guides and API reference.

## 🛠️ Examples

Check out our [examples](examples/) directory for more usage examples:

- [Basic API](examples/basic_app.py)
- [CORS Support](examples/cors_app.py)
- [Authentication](examples/auth_app.py)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by FastAPI and Starlette
- Built with modern Python features
- Community-driven development

## 📬 Contact

If you have any questions or suggestions, feel free to open an issue or reach out to the maintainers.

---

Made with ❤️ by the QakeAPI team 