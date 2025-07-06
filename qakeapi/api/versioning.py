"""API versioning system for QakeAPI."""

import re
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum

logger = logging.getLogger(__name__)

class VersionStrategy(ABC):
    """Abstract base class for version strategies."""
    
    @abstractmethod
    def extract_version(self, request: Any) -> Optional[str]:
        """Extract version from request."""
        pass
    
    @abstractmethod
    def is_version_supported(self, version: str) -> bool:
        """Check if version is supported."""
        pass
    
    @abstractmethod
    def get_default_version(self) -> str:
        """Get default version."""
        pass

class PathVersionStrategy(VersionStrategy):
    """Path-based versioning strategy (/v1/, /v2/)."""
    
    def __init__(self, supported_versions: List[str], default_version: str = "v1"):
        self.supported_versions = supported_versions
        self.default_version = default_version
        self.version_pattern = re.compile(r'^/v(\d+)/')
        logger.debug(f"Initialized PathVersionStrategy with versions: {supported_versions}")
    
    def extract_version(self, request: Any) -> Optional[str]:
        """Extract version from URL path."""
        path = getattr(request, 'path', '')
        match = self.version_pattern.match(path)
        if match:
            version = f"v{match.group(1)}"
            logger.debug(f"Extracted version from path: {version}")
            return version
        return None
    
    def is_version_supported(self, version: str) -> bool:
        """Check if version is supported."""
        return version in self.supported_versions
    
    def get_default_version(self) -> str:
        """Get default version."""
        return self.default_version

class HeaderVersionStrategy(VersionStrategy):
    """Header-based versioning strategy (Accept-Version header)."""
    
    def __init__(self, supported_versions: List[str], default_version: str = "v1"):
        self.supported_versions = supported_versions
        self.default_version = default_version
        logger.debug(f"Initialized HeaderVersionStrategy with versions: {supported_versions}")
    
    def extract_version(self, request: Any) -> Optional[str]:
        """Extract version from Accept-Version header."""
        headers = getattr(request, 'headers', {})
        version_header = headers.get(b'accept-version', b'').decode('utf-8')
        if version_header:
            logger.debug(f"Extracted version from header: {version_header}")
            return version_header
        return version_header  # Return empty string if header is empty
    
    def is_version_supported(self, version: str) -> bool:
        """Check if version is supported."""
        return version in self.supported_versions
    
    def get_default_version(self) -> str:
        """Get default version."""
        return self.default_version

class CombinedVersionStrategy(VersionStrategy):
    """Combined versioning strategy (path + header)."""
    
    def __init__(self, path_strategy: PathVersionStrategy, header_strategy: HeaderVersionStrategy):
        self.path_strategy = path_strategy
        self.header_strategy = header_strategy
        self.supported_versions = list(set(path_strategy.supported_versions + header_strategy.supported_versions))
        self.default_version = path_strategy.default_version
        logger.debug(f"Initialized CombinedVersionStrategy with versions: {self.supported_versions}")
    
    def extract_version(self, request: Any) -> Optional[str]:
        """Extract version from path first, then header."""
        # Try path first
        version = self.path_strategy.extract_version(request)
        if version:
            return version
        
        # Try header
        version = self.header_strategy.extract_version(request)
        if version:
            return version
        
        return None
    
    def is_version_supported(self, version: str) -> bool:
        """Check if version is supported."""
        return version in self.supported_versions
    
    def get_default_version(self) -> str:
        """Get default version."""
        return self.default_version

@dataclass
class VersionInfo:
    """Information about API version."""
    version: str
    release_date: datetime
    sunset_date: Optional[datetime] = None
    deprecated: bool = False
    breaking_changes: List[str] = None
    new_features: List[str] = None
    bug_fixes: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "release_date": self.release_date.isoformat() if self.release_date else None,
            "sunset_date": self.sunset_date.isoformat() if self.sunset_date else None,
            "deprecated": self.deprecated,
            "breaking_changes": self.breaking_changes or [],
            "new_features": self.new_features or [],
            "bug_fixes": self.bug_fixes or []
        }

class APIVersionManager:
    """Manager for API versioning."""
    
    def __init__(self, 
                 strategy: VersionStrategy,
                 versions_info: Optional[Dict[str, VersionInfo]] = None):
        self.strategy = strategy
        self.versions_info = versions_info or {}
        self.version_handlers: Dict[str, Dict[str, Callable]] = {}
        self.middleware_handlers: Dict[str, List[Callable]] = {}
        logger.debug("Initialized APIVersionManager")
    
    def register_version_handler(self, version: str, path: str, handler: Callable) -> None:
        """Register handler for specific version and path."""
        if version not in self.version_handlers:
            self.version_handlers[version] = {}
        self.version_handlers[version][path] = handler
        logger.debug(f"Registered handler for version {version}, path {path}")
    
    def get_version_handler(self, version: str, path: str) -> Optional[Callable]:
        """Get handler for specific version and path."""
        if version in self.version_handlers:
            return self.version_handlers[version].get(path)
        return None
    
    def get_supported_versions(self) -> List[str]:
        """Get list of supported versions."""
        return self.strategy.supported_versions
    
    def is_version_deprecated(self, version: str) -> bool:
        """Check if version is deprecated."""
        if version in self.versions_info:
            return self.versions_info[version].deprecated
        return False
    
    def get_version_info(self, version: str) -> Optional[VersionInfo]:
        """Get version information."""
        return self.versions_info.get(version)
    
    def add_version_info(self, version: str, info: VersionInfo) -> None:
        """Add version information."""
        self.versions_info[version] = info
        logger.debug(f"Added version info for {version}")
    
    def get_version_from_request(self, request: Any) -> str:
        """Get version from request using strategy."""
        version = self.strategy.extract_version(request)
        if version and self.strategy.is_version_supported(version):
            return version
        return self.strategy.get_default_version()
    
    def get_version_compatibility_matrix(self) -> Dict[str, Dict[str, bool]]:
        """Get version compatibility matrix."""
        matrix = {}
        versions = self.get_supported_versions()
        
        for v1 in versions:
            matrix[v1] = {}
            for v2 in versions:
                # Simple compatibility logic - can be enhanced
                matrix[v1][v2] = v1 == v2 or self._are_versions_compatible(v1, v2)
        
        return matrix
    
    def _are_versions_compatible(self, version1: str, version2: str) -> bool:
        """Check if two versions are compatible."""
        # Extract major version numbers
        v1_major = int(version1[1:].split('.')[0]) if version1.startswith('v') else 1
        v2_major = int(version2[1:].split('.')[0]) if version2.startswith('v') else 1
        
        # Same major version means compatible
        return v1_major == v2_major
    
    def generate_changelog(self) -> Dict[str, Any]:
        """Generate API changelog."""
        changelog = {
            "versions": {},
            "latest_version": max(self.get_supported_versions()),
            "deprecated_versions": [],
            "sunset_versions": []
        }
        
        for version, info in self.versions_info.items():
            changelog["versions"][version] = {
                "release_date": info.release_date.isoformat(),
                "deprecated": info.deprecated,
                "sunset_date": info.sunset_date.isoformat() if info.sunset_date else None,
                "breaking_changes": info.breaking_changes or [],
                "new_features": info.new_features or [],
                "bug_fixes": info.bug_fixes or []
            }
            
            if info.deprecated:
                changelog["deprecated_versions"].append(version)
            
            if info.sunset_date and info.sunset_date <= datetime.now():
                changelog["sunset_versions"].append(version)
        
        return changelog

def version_route(version: str, path: str):
    """Decorator for version-specific routes."""
    def decorator(handler: Callable) -> Callable:
        handler.version_info = {"version": version, "path": path}
        return handler
    return decorator 