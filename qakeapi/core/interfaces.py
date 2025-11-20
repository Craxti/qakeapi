from typing import Any, Dict, List, Optional, Protocol

class UserProtocol(Protocol):
    """Base protocol for User objects"""
    @property
    def username(self) -> str:
        ...
    
    @property
    def roles(self) -> List[str]:
        ...
    
    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        ... 