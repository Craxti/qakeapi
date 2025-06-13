"""
QakeAPI - A lightweight ASGI web framework for building fast web APIs with Python
"""

__version__ = "0.1.0"

# Core components
from .core.application import Application
from .core.background import BackgroundTask
from .core.dependencies import Dependency, inject
from .core.files import UploadFile
from .core.requests import Request
from .core.responses import Response
from .core.router import Router

# Make commonly used classes available at package level
__all__ = [
    "Application",
    "Response",
    "Request",
    "Router",
    "Dependency",
    "inject",
    "BackgroundTask",
    "UploadFile",
]
