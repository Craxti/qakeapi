"""API module for QakeAPI framework."""

from .deprecation import DeprecationManager, DeprecationWarning
from .versioning import (
    APIVersionManager,
    HeaderVersionStrategy,
    PathVersionStrategy,
    VersionStrategy,
)

__all__ = [
    "APIVersionManager",
    "VersionStrategy",
    "PathVersionStrategy",
    "HeaderVersionStrategy",
    "DeprecationManager",
    "DeprecationWarning",
]
