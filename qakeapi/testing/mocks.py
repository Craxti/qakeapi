"""
Mock services and external API testing for QakeAPI.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Callable, Union, AsyncGenerator
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
import aiohttp
from aiohttp import web

logger = logging.getLogger(__name__)


@dataclass
class MockResponse:
    """Mock HTTP response."""
    status: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    delay: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status,
            "headers": self.headers,
            "body": self.body,
            "delay": self.delay
        }


class MockService:
    """Mock service for testing."""
    
    def __init__(self, name: str):
        self.name = name
        self._responses: Dict[str, MockResponse] = {}
        self._call_history: List[Dict[str, Any]] = []
        self._default_response = MockResponse()
    
    def add_response(self, method: str, path: str, response: MockResponse) -> None:
        """Add mock response for method and path."""
        key = f"{method.upper()}:{path}"
        self._responses[key] = response
        logger.debug(f"Added mock response for {key}")
    
    def set_default_response(self, response: MockResponse) -> None:
        """Set default response for unmatched requests."""
        self._default_response = response
    
    def get_response(self, method: str, path: str) -> MockResponse:
        """Get response for method and path."""
        key = f"{method.upper()}:{path}"
        return self._responses.get(key, self._default_response)
    
    def record_call(self, method: str, path: str, headers: Dict[str, str], body: Any) -> None:
        """Record service call."""
        call = {
            "method": method,
            "path": path,
            "headers": headers,
            "body": body,
            "timestamp": asyncio.get_event_loop().time()
        }
        self._call_history.append(call)
        logger.debug(f"Recorded call: {method} {path}")
    
    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get call history."""
        return self._call_history.copy()
    
    def clear_history(self) -> None:
        """Clear call history."""
        self._call_history.clear()
    
    def get_call_count(self, method: str = None, path: str = None) -> int:
        """Get call count for method and path."""
        if method is None and path is None:
            return len(self._call_history)
        
        count = 0
        for call in self._call_history:
            if method and call["method"] != method:
                continue
            if path and call["path"] != path:
                continue
            count += 1
        
        return count


class MockExternalAPI:
    """Mock external API for testing."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.services: Dict[str, MockService] = {}
        self._server: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
    
    def add_service(self, service: MockService) -> None:
        """Add mock service."""
        self.services[service.name] = service
    
    def get_service(self, name: str) -> MockService:
        """Get service by name."""
        if name not in self.services:
            raise ValueError(f"Service '{name}' not found")
        return self.services[name]
    
    async def start(self, port: int = 8080) -> None:
        """Start mock API server."""
        self._server = web.Application()
        
        # Add routes for all services
        for service_name, service in self.services.items():
            self._server.router.add_route(
                "*", 
                f"/{service_name}/{{path:.*}}", 
                self._handle_request
            )
        
        self._runner = web.AppRunner(self._server)
        await self._runner.setup()
        
        self._site = web.TCPSite(self._runner, "localhost", port)
        await self._site.start()
        
        logger.info(f"Mock API server started on http://localhost:{port}")
    
    async def stop(self) -> None:
        """Stop mock API server."""
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()
        
        logger.info("Mock API server stopped")
    
    async def _handle_request(self, request: web.Request) -> web.Response:
        """Handle incoming request."""
        path = request.match_info["path"]
        method = request.method
        headers = dict(request.headers)
        
        # Parse body
        try:
            body = await request.json()
        except:
            body = await request.text()
        
        # Find service from path
        service_name = path.split("/")[0] if path else ""
        if service_name not in self.services:
            return web.Response(status=404, text="Service not found")
        
        service = self.services[service_name]
        service_path = "/".join(path.split("/")[1:]) if len(path.split("/")) > 1 else ""
        
        # Record call
        service.record_call(method, service_path, headers, body)
        
        # Get response
        response = service.get_response(method, service_path)
        
        # Add delay if specified
        if response.delay > 0:
            await asyncio.sleep(response.delay)
        
        # Return response
        if isinstance(response.body, dict):
            return web.json_response(
                response.body, 
                status=response.status,
                headers=response.headers
            )
        else:
            return web.Response(
                text=str(response.body),
                status=response.status,
                headers=response.headers
            )


class MockHTTPClient:
    """Mock HTTP client for testing."""
    
    def __init__(self, mock_api: MockExternalAPI):
        self.mock_api = mock_api
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> aiohttp.ClientResponse:
        """Mock GET request."""
        return await self._request("GET", url, headers=headers)
    
    async def post(self, url: str, data: Any = None, headers: Optional[Dict[str, str]] = None) -> aiohttp.ClientResponse:
        """Mock POST request."""
        return await self._request("POST", url, data=data, headers=headers)
    
    async def put(self, url: str, data: Any = None, headers: Optional[Dict[str, str]] = None) -> aiohttp.ClientResponse:
        """Mock PUT request."""
        return await self._request("PUT", url, data=data, headers=headers)
    
    async def delete(self, url: str, headers: Optional[Dict[str, str]] = None) -> aiohttp.ClientResponse:
        """Mock DELETE request."""
        return await self._request("DELETE", url, headers=headers)
    
    async def _request(self, method: str, url: str, data: Any = None, headers: Optional[Dict[str, str]] = None) -> aiohttp.ClientResponse:
        """Mock HTTP request."""
        # Create mock response
        mock_response = AsyncMock(spec=aiohttp.ClientResponse)
        
        # Parse URL to find service and path
        parsed_url = url.replace(self.mock_api.base_url, "").strip("/")
        if not parsed_url:
            mock_response.status = 404
            mock_response.text = AsyncMock(return_value="Not found")
            return mock_response
        
        service_name = parsed_url.split("/")[0]
        service_path = "/".join(parsed_url.split("/")[1:]) if len(parsed_url.split("/")) > 1 else ""
        
        if service_name not in self.mock_api.services:
            mock_response.status = 404
            mock_response.text = AsyncMock(return_value="Service not found")
            return mock_response
        
        service = self.mock_api.services[service_name]
        
        # Record call
        service.record_call(method, service_path, headers or {}, data)
        
        # Get response
        response = service.get_response(method, service_path)
        
        # Setup mock response
        mock_response.status = response.status
        mock_response.headers = response.headers
        
        if isinstance(response.body, dict):
            mock_response.json = AsyncMock(return_value=response.body)
            mock_response.text = AsyncMock(return_value=json.dumps(response.body))
        else:
            mock_response.text = AsyncMock(return_value=str(response.body))
            mock_response.json = AsyncMock(side_effect=ValueError("Not JSON"))
        
        return mock_response


# Predefined mock services
def create_user_service() -> MockService:
    """Create mock user service."""
    service = MockService("users")
    
    # GET /users
    service.add_response("GET", "/users", MockResponse(
        status=200,
        body={"users": [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
        ]}
    ))
    
    # GET /users/{id}
    service.add_response("GET", "/users/1", MockResponse(
        status=200,
        body={"id": 1, "name": "John Doe", "email": "john@example.com"}
    ))
    
    # POST /users
    service.add_response("POST", "/users", MockResponse(
        status=201,
        body={"id": 3, "name": "New User", "email": "new@example.com"}
    ))
    
    return service


def create_payment_service() -> MockService:
    """Create mock payment service."""
    service = MockService("payments")
    
    # POST /payments
    service.add_response("POST", "/payments", MockResponse(
        status=200,
        body={"transaction_id": "txn_123", "status": "success"}
    ))
    
    # GET /payments/{id}
    service.add_response("GET", "/payments/txn_123", MockResponse(
        status=200,
        body={"transaction_id": "txn_123", "status": "success", "amount": 100.00}
    ))
    
    return service


def create_email_service() -> MockService:
    """Create mock email service."""
    service = MockService("email")
    
    # POST /email/send
    service.add_response("POST", "/email/send", MockResponse(
        status=200,
        body={"message_id": "msg_456", "status": "sent"}
    ))
    
    return service


# Context manager for mock API testing
@asynccontextmanager
async def mock_api(services: Optional[List[MockService]] = None, port: int = 8080):
    """Context manager for mock API testing."""
    api = MockExternalAPI(f"http://localhost:{port}")
    
    # Add default services if none provided
    if services is None:
        services = [create_user_service(), create_payment_service(), create_email_service()]
    
    for service in services:
        api.add_service(service)
    
    try:
        await api.start(port)
        yield api
    finally:
        await api.stop()


# Decorator for mock service testing
def with_mock_service(service_name: str, service_factory: Callable[[], MockService]):
    """Decorator for mock service testing."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Create mock API
            api = MockExternalAPI()
            service = service_factory()
            api.add_service(service)
            
            try:
                # Start mock API
                await api.start()
                
                # Add to kwargs
                kwargs['mock_api'] = api
                kwargs['mock_service'] = service
                
                # Run test
                result = await func(*args, **kwargs)
                
                return result
            finally:
                # Stop mock API
                await api.stop()
        
        return wrapper
    return decorator 