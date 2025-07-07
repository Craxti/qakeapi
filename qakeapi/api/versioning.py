"""
Enhanced API Versioning System following SOLID principles.

Provides comprehensive API versioning with multiple strategies:
- Path-based versioning (/v1/, /v2/)
- Header-based versioning (Accept-Version)
- Deprecation warnings and sunset dates
- Version compatibility matrix
"""

import re
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any, Union
from functools import wraps

logger = logging.getLogger(__name__)


class VersionStrategy(Enum):
    """API versioning strategies."""
    PATH = "path"
    HEADER = "header"
    QUERY = "query"
    CUSTOM = "custom"


class VersionStatus(Enum):
    """Version status enumeration."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"
    EXPERIMENTAL = "experimental"


@dataclass
class VersionInfo:
    """Information about API version."""
    version: str
    status: VersionStatus
    release_date: Optional[date] = None
    deprecation_date: Optional[date] = None
    sunset_date: Optional[date] = None
    description: Optional[str] = None
    breaking_changes: List[str] = field(default_factory=list)
    new_features: List[str] = field(default_factory=list)
    bug_fixes: List[str] = field(default_factory=list)


@dataclass
class DeprecationWarning:
    """Deprecation warning information."""
    version: str
    message: str
    deprecation_date: date
    sunset_date: Optional[date] = None
    migration_guide: Optional[str] = None
    alternative_endpoint: Optional[str] = None


class VersionStrategyInterface(ABC):
    """Abstract interface for version strategies following SOLID principles."""
    
    @abstractmethod
    def extract_version(self, request: Any) -> Optional[str]:
        """Extract version from request."""
        pass
    
    @abstractmethod
    def is_version_valid(self, version: str) -> bool:
        """Check if version is valid."""
        pass
    
    @abstractmethod
    def get_default_version(self) -> str:
        """Get default version."""
        pass


class PathVersionStrategy(VersionStrategyInterface):
    """Path-based versioning strategy (/v1/, /v2/)."""
    
    def __init__(self, versions: List[str], default_version: str = "v1"):
        self.versions = set(versions)
        self.default_version = default_version
        self.version_pattern = re.compile(r'^/v(\d+)/')
    
    def extract_version(self, request: Any) -> Optional[str]:
        """Extract version from path."""
        path = getattr(request, 'path', '')
        match = self.version_pattern.match(path)
        if match:
            version = f"v{match.group(1)}"
            return version if version in self.versions else None
        return None
    
    def is_version_valid(self, version: str) -> bool:
        """Check if version is valid."""
        return version in self.versions
    
    def get_default_version(self) -> str:
        """Get default version."""
        return self.default_version


class HeaderVersionStrategy(VersionStrategyInterface):
    """Header-based versioning strategy (Accept-Version)."""
    
    def __init__(self, versions: List[str], default_version: str = "v1", header_name: str = "Accept-Version"):
        self.versions = set(versions)
        self.default_version = default_version
        self.header_name = header_name
    
    def extract_version(self, request: Any) -> Optional[str]:
        """Extract version from header."""
        headers = getattr(request, 'headers', {})
        version_header = headers.get(self.header_name.lower(), '')
        
        if version_header:
            # Parse Accept-Version header (e.g., "v1, v2;q=0.9")
            versions = [v.strip().split(';')[0] for v in version_header.split(',')]
            for version in versions:
                if version in self.versions:
                    return version
        
        return None
    
    def is_version_valid(self, version: str) -> bool:
        """Check if version is valid."""
        return version in self.versions
    
    def get_default_version(self) -> str:
        """Get default version."""
        return self.default_version


class QueryVersionStrategy(VersionStrategyInterface):
    """Query parameter versioning strategy (?version=v1)."""
    
    def __init__(self, versions: List[str], default_version: str = "v1", param_name: str = "version"):
        self.versions = set(versions)
        self.default_version = default_version
        self.param_name = param_name
    
    def extract_version(self, request: Any) -> Optional[str]:
        """Extract version from query parameters."""
        query_params = getattr(request, 'query_params', {})
        version = query_params.get(self.param_name)
        
        if version and version in self.versions:
            return version
        
        return None
    
    def is_version_valid(self, version: str) -> bool:
        """Check if version is valid."""
        return version in self.versions
    
    def get_default_version(self) -> str:
        """Get default version."""
        return self.default_version


class APIVersionManager:
    """Main API version manager following SOLID principles."""
    
    def __init__(self, default_strategy: VersionStrategy = VersionStrategy.PATH):
        self.strategies: Dict[VersionStrategy, VersionStrategyInterface] = {}
        self.default_strategy = default_strategy
        self.versions: Dict[str, VersionInfo] = {}
        self.deprecation_warnings: Dict[str, DeprecationWarning] = {}
        self.compatibility_matrix: Dict[str, Set[str]] = {}
        
        # Initialize default strategies
        self._init_default_strategies()
    
    def _init_default_strategies(self):
        """Initialize default versioning strategies."""
        # This will be configured by the application
        pass
    
    def add_strategy(self, strategy_type: VersionStrategy, strategy: VersionStrategyInterface):
        """Add versioning strategy."""
        self.strategies[strategy_type] = strategy
    
    def register_version(self, version_info: VersionInfo):
        """Register a new API version."""
        self.versions[version_info.version] = version_info
        
        if version_info.status == VersionStatus.DEPRECATED:
            self._add_deprecation_warning(version_info)
    
    def _add_deprecation_warning(self, version_info: VersionInfo):
        """Add deprecation warning for version."""
        warning = DeprecationWarning(
            version=version_info.version,
            message=f"API version {version_info.version} is deprecated",
            deprecation_date=version_info.deprecation_date or date.today(),
            sunset_date=version_info.sunset_date
        )
        self.deprecation_warnings[version_info.version] = warning
    
    def get_version_info(self, version: str) -> Optional[VersionInfo]:
        """Get version information."""
        return self.versions.get(version)
    
    def is_version_deprecated(self, version: str) -> bool:
        """Check if version is deprecated."""
        version_info = self.get_version_info(version)
        return version_info and version_info.status == VersionStatus.DEPRECATED
    
    def is_version_sunset(self, version: str) -> bool:
        """Check if version has reached sunset date."""
        version_info = self.get_version_info(version)
        if not version_info or not version_info.sunset_date:
            return False
        
        return date.today() >= version_info.sunset_date
    
    def get_deprecation_warning(self, version: str) -> Optional[DeprecationWarning]:
        """Get deprecation warning for version."""
        return self.deprecation_warnings.get(version)
    
    def extract_version(self, request: Any, strategy: Optional[VersionStrategy] = None) -> str:
        """Extract version from request using specified strategy."""
        strategy_type = strategy or self.default_strategy
        strategy_impl = self.strategies.get(strategy_type)
        
        if not strategy_impl:
            raise ValueError(f"Strategy {strategy_type} not found")
        
        version = strategy_impl.extract_version(request)
        if version and strategy_impl.is_version_valid(version):
            return version
        
        return strategy_impl.get_default_version()
    
    def add_compatibility(self, version: str, compatible_versions: List[str]):
        """Add version compatibility information."""
        self.compatibility_matrix[version] = set(compatible_versions)
    
    def is_compatible(self, version1: str, version2: str) -> bool:
        """Check if two versions are compatible."""
        if version1 == version2:
            return True
        
        compatible_versions = self.compatibility_matrix.get(version1, set())
        return version2 in compatible_versions
    
    def get_all_versions(self) -> List[str]:
        """Get all registered versions."""
        return list(self.versions.keys())
    
    def get_active_versions(self) -> List[str]:
        """Get all active versions."""
        return [
            version for version, info in self.versions.items()
            if info.status == VersionStatus.ACTIVE
        ]
    
    def get_deprecated_versions(self) -> List[str]:
        """Get all deprecated versions."""
        return [
            version for version, info in self.versions.items()
            if info.status == VersionStatus.DEPRECATED
        ]


class VersionMiddleware:
    """Middleware for handling API versioning."""
    
    def __init__(self, version_manager: APIVersionManager):
        self.version_manager = version_manager
    
    async def __call__(self, scope, receive, send):
        """Process request with versioning."""
        # Create a mock request object for version extraction
        # In real implementation, this would be the actual request object
        request = type('Request', (), {
            'path': scope.get('path', ''),
            'headers': dict(scope.get('headers', [])),
            'query_params': dict(scope.get('query_string', b'').decode().split('&'))
        })()
        
        # Extract version
        version = self.version_manager.extract_version(request)
        
        # Add version to scope
        scope['api_version'] = version
        
        # Check for deprecation warnings
        if self.version_manager.is_version_deprecated(version):
            warning = self.version_manager.get_deprecation_warning(version)
            if warning:
                # Add deprecation warning to response headers
                # This would be handled in the response middleware
                scope['deprecation_warning'] = warning
        
        # Check for sunset
        if self.version_manager.is_version_sunset(version):
            # Return 410 Gone for sunset versions
            await send({
                'type': 'http.response.start',
                'status': 410,
                'headers': [
                    (b'content-type', b'application/json'),
                    (b'content-length', b'0')
                ]
            })
            await send({
                'type': 'http.response.body',
                'body': b''
            })
            return
        
        # Continue with normal processing
        return await self.app(scope, receive, send)


def version_required(version: str):
    """Decorator to require specific API version."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # In real implementation, this would check the request version
            # For now, we'll just add version info to the function
            wrapper.required_version = version
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def deprecated_version(version: str, sunset_date: Optional[date] = None):
    """Decorator to mark endpoint as deprecated."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Add deprecation info to function
            wrapper.deprecated_version = version
            wrapper.sunset_date = sunset_date
            return await func(*args, **kwargs)
        return wrapper
    return decorator 


class VersionCompatibilityChecker:
    """Utility for checking version compatibility."""
    
    def __init__(self, version_manager: APIVersionManager):
        self.version_manager = version_manager
    
    def check_compatibility(self, client_version: str, server_version: str) -> bool:
        """Check if client and server versions are compatible."""
        return self.version_manager.is_compatible(client_version, server_version)
    
    def get_migration_path(self, from_version: str, to_version: str) -> List[str]:
        """Get migration path between versions."""
        # This would implement a graph algorithm to find the shortest path
        # between versions in the compatibility matrix
        # For now, return a simple path
        return [from_version, to_version]


# Factory for creating version managers
class VersionManagerFactory:
    """Factory for creating version managers with common configurations."""
    
    @staticmethod
    def create_path_based_manager(versions: List[str], default_version: str = "v1") -> APIVersionManager:
        """Create path-based version manager."""
        manager = APIVersionManager(VersionStrategy.PATH)
        strategy = PathVersionStrategy(versions, default_version)
        manager.add_strategy(VersionStrategy.PATH, strategy)
        return manager
    
    @staticmethod
    def create_header_based_manager(versions: List[str], default_version: str = "v1") -> APIVersionManager:
        """Create header-based version manager."""
        manager = APIVersionManager(VersionStrategy.HEADER)
        strategy = HeaderVersionStrategy(versions, default_version)
        manager.add_strategy(VersionStrategy.HEADER, strategy)
        return manager
    
    @staticmethod
    def create_multi_strategy_manager(versions: List[str], default_version: str = "v1") -> APIVersionManager:
        """Create manager with multiple strategies."""
        manager = APIVersionManager(VersionStrategy.PATH)
        
        # Add path strategy
        path_strategy = PathVersionStrategy(versions, default_version)
        manager.add_strategy(VersionStrategy.PATH, path_strategy)
        
        # Add header strategy
        header_strategy = HeaderVersionStrategy(versions, default_version)
        manager.add_strategy(VersionStrategy.HEADER, header_strategy)
        
        # Add query strategy
        query_strategy = QueryVersionStrategy(versions, default_version)
        manager.add_strategy(VersionStrategy.QUERY, query_strategy)
        
        return manager 