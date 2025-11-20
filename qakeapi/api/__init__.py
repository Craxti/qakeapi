"""API module for QakeAPI framework."""

from .versioning import APIVersionManager, VersionStrategy, PathVersionStrategy, HeaderVersionStrategy
from .deprecation import DeprecationManager, DeprecationWarning

__all__ = [
    "APIVersionManager",
    "VersionStrategy", 
    "PathVersionStrategy",
    "HeaderVersionStrategy",
    "DeprecationManager",
    "DeprecationWarning"
] 