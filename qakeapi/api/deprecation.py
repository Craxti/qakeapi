"""Deprecation management system for QakeAPI."""

import logging
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

logger = logging.getLogger(__name__)

class DeprecationLevel(Enum):
    """Deprecation levels."""
    WARNING = "warning"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"

@dataclass
class DeprecationInfo:
    """Information about a deprecated feature."""
    feature: str
    version: str
    deprecation_date: datetime
    sunset_date: Optional[datetime] = None
    replacement: Optional[str] = None
    migration_guide: Optional[str] = None
    level: str = "warning"

@dataclass
class DeprecationWarning:
    """Deprecation warning information."""
    feature: str
    version: str
    deprecation_date: datetime
    sunset_date: Optional[datetime] = None
    replacement: Optional[str] = None
    migration_guide: Optional[str] = None
    level: DeprecationLevel = DeprecationLevel.WARNING

class DeprecationManager:
    """Manager for handling deprecation warnings and sunset dates."""
    
    def __init__(self):
        self.deprecations: Dict[str, DeprecationWarning] = {}
        self.enabled = True
        logger.debug("Initialized DeprecationManager")
    
    def add_deprecation(self, feature: str, deprecation: DeprecationInfo) -> None:
        """Add a deprecation warning."""
        self.deprecations[feature] = deprecation
        logger.debug(f"Added deprecation for {feature}")
    
    def is_deprecated(self, feature: str) -> bool:
        """Check if feature is deprecated."""
        if feature in self.deprecations:
            deprecation = self.deprecations[feature]
            return deprecation.level in [DeprecationLevel.DEPRECATED, DeprecationLevel.SUNSET]
        return False
    
    def is_sunset(self, feature: str) -> bool:
        """Check if feature is sunset (no longer supported)."""
        if feature in self.deprecations:
            deprecation = self.deprecations[feature]
            if deprecation.sunset_date:
                return datetime.now() >= deprecation.sunset_date
        return False
    
    def get_deprecation_info(self, feature: str) -> Optional[DeprecationInfo]:
        """Get deprecation information for feature."""
        return self.deprecations.get(feature)
    
    def check_deprecation(self, feature: str, request: Any = None) -> Optional[str]:
        """Check deprecation and return warning message if needed."""
        if not self.enabled or feature not in self.deprecations:
            return None
        
        deprecation = self.deprecations[feature]
        now = datetime.now()
        
        # Check if feature is sunset
        if deprecation.sunset_date and now >= deprecation.sunset_date:
            raise DeprecationError(
                f"Feature '{feature}' has been sunset on {deprecation.sunset_date}"
            )
        
        # Check if feature is deprecated
        if deprecation.deprecation_date and now >= deprecation.deprecation_date:
            warning_msg = self._generate_warning_message(deprecation)
            logger.warning(warning_msg)
            
            # Add deprecation header to response if request is provided
            if request and hasattr(request, 'add_header'):
                request.add_header('X-API-Deprecation', warning_msg)
            
            return warning_msg
        
        return None
    
    def _generate_warning_message(self, deprecation: DeprecationWarning) -> str:
        """Generate deprecation warning message."""
        msg = f"Feature '{deprecation.feature}' is deprecated since version {deprecation.version}"
        
        if deprecation.sunset_date:
            msg += f" and will be removed on {deprecation.sunset_date.strftime('%Y-%m-%d')}"
        
        if deprecation.replacement:
            msg += f". Use '{deprecation.replacement}' instead."
        
        if deprecation.migration_guide:
            msg += f" See migration guide: {deprecation.migration_guide}"
        
        return msg
    
    def get_all_deprecations(self) -> List[DeprecationInfo]:
        """Get all deprecation warnings."""
        return list(self.deprecations.values())
    
    def get_active_deprecations(self) -> List[Dict[str, Any]]:
        """Get active deprecation warnings."""
        now = datetime.now()
        active = []
        for feature, dep in self.deprecations.items():
            if dep.deprecation_date and now >= dep.deprecation_date:
                active.append({
                    "feature": feature,
                    "version": dep.version,
                    "deprecation_date": dep.deprecation_date.isoformat(),
                    "sunset_date": dep.sunset_date.isoformat() if dep.sunset_date else None,
                    "replacement": dep.replacement,
                    "migration_guide": dep.migration_guide
                })
        return active
    
    def get_sunset_features(self) -> List[str]:
        """Get features that are sunset."""
        return [feature for feature in self.deprecations.keys() if self.is_sunset(feature)]
    
    def enable(self) -> None:
        """Enable deprecation warnings."""
        self.enabled = True
        logger.debug("Deprecation warnings enabled")
    
    def disable(self) -> None:
        """Disable deprecation warnings."""
        self.enabled = False
        logger.debug("Deprecation warnings disabled")

class DeprecationError(Exception):
    """Exception raised when using sunset features."""
    pass

def deprecated(feature: str, 
               version: str, 
               deprecation_date: datetime,
               sunset_date: Optional[datetime] = None,
               replacement: Optional[str] = None,
               migration_guide: Optional[str] = None):
    """Decorator to mark features as deprecated."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Get deprecation manager from request if available
            deprecation_manager = None
            for arg in args:
                if hasattr(arg, 'app') and hasattr(arg.app, 'deprecation_manager'):
                    deprecation_manager = arg.app.deprecation_manager
                    break
            
            if deprecation_manager:
                deprecation_manager.check_deprecation(feature, args[0] if args else None)
            
            return func(*args, **kwargs)
        
        # Add deprecation info to function
        wrapper.deprecation_info = {
            "feature": feature,
            "version": version,
            "deprecation_date": deprecation_date,
            "sunset_date": sunset_date,
            "replacement": replacement,
            "migration_guide": migration_guide
        }
        
        return wrapper
    return decorator 