"""
QakeAPI - A lightweight ASGI web framework for building fast web APIs with Python
"""

__version__ = "0.1.0"

# Core components
from .core.application import Application
from .core.responses import Response
from .core.requests import Request
from .core.router import Router
from .core.dependencies import Dependency, inject
from .core.background import BackgroundTask
from .core.files import UploadFile

# Make commonly used classes available at package level
__all__ = [
    "Application",
    "Response",
    "Request",
    "Router",
    "Dependency",
    "inject",
    "BackgroundTask",
    "UploadFile"
] 