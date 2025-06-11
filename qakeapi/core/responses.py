from typing import Any, Dict, List, Optional, Union, Tuple, AsyncGenerator, AsyncIterable
import json
from datetime import datetime, timedelta
from http.cookies import SimpleCookie

class Response:
    """HTTP Response"""
    
    def __init__(
        self,
        content: Union[str, bytes, dict],
        status: int = 200,
        headers: Optional[List[Tuple[bytes, bytes]]] = None
    ):
        self.content = content
        self.status = status
        self.headers = headers or []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to ASGI response dict"""
        if isinstance(self.content, dict):
            body = json.dumps(self.content).encode()
            if not any(h[0] == b"content-type" for h in self.headers):
                self.headers.append((b"content-type", b"application/json"))
        elif isinstance(self.content, str):
            body = self.content.encode()
            if not any(h[0] == b"content-type" for h in self.headers):
                self.headers.append((b"content-type", b"text/plain"))
        else:
            body = self.content
            
        return {
            "status": self.status,
            "headers": self.headers,
            "body": body
        }
        
    @classmethod
    def json(cls, content: dict, status: int = 200) -> "Response":
        """Create JSON response"""
        return cls(content, status=status)
        
    @classmethod
    def text(cls, content: str, status: int = 200) -> "Response":
        """Create text response"""
        return cls(content, status=status)
        
    @property
    async def body(self) -> bytes:
        """Получить тело ответа в виде байтов"""
        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, str):
            return self.content.encode("utf-8")
        else:
            return json.dumps(self.content).encode("utf-8")
            
    @property
    def headers_list(self) -> List[Tuple[bytes, bytes]]:
        """Получить заголовки в виде списка кортежей"""
        headers = []
        
        # Добавляем Content-Type, если не указан
        if "content-type" not in [h[0].decode().lower() for h in self.headers]:
            media_type = self._get_media_type()
            headers.append((b"content-type", media_type.encode()))
            
        # Добавляем остальные заголовки
        for name, value in self.headers:
            headers.append((name, value))
            
        return headers
        
    def _get_media_type(self) -> str:
        """Определить Content-Type на основе содержимого"""
        if isinstance(self.content, bytes):
            return "application/octet-stream"
        elif isinstance(self.content, str):
            return "text/plain"
        else:
            return "application/json"
            
    def set_cookie(
        self,
        key: str,
        value: str = "",
        max_age: Optional[int] = None,
        expires: Optional[int] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: str = "lax"
    ) -> None:
        """Установить cookie"""
        self.headers.append((b"set-cookie", f"{key}={value}; Path={path}".encode()))
        if max_age is not None:
            self.headers.append((b"set-cookie", f"Max-Age={max_age}".encode()))
        if expires is not None:
            self.headers.append((b"set-cookie", f"Expires={expires}".encode()))
        if domain is not None:
            self.headers.append((b"set-cookie", f"Domain={domain}".encode()))
        if secure:
            self.headers.append((b"set-cookie", b"Secure"))
        if httponly:
            self.headers.append((b"set-cookie", b"HttpOnly"))
        if samesite is not None:
            self.headers.append((b"set-cookie", f"SameSite={samesite}".encode()))
            
    def delete_cookie(self, key: str, path: str = "/", domain: Optional[str] = None) -> None:
        """Удалить cookie"""
        self.set_cookie(key, "", max_age=0, path=path, domain=domain)
        
    @classmethod
    def html(
        cls,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ) -> "Response":
        """Создать HTML ответ"""
        return cls(content, status_code, headers)
        
    @classmethod
    def redirect(
        cls,
        url: str,
        status_code: int = 302,
        headers: Optional[Dict[str, str]] = None
    ) -> "Response":
        """Создать редирект"""
        headers = headers or {}
        headers["location"] = url
        return cls(b"", status_code, headers)
        
    @classmethod
    def stream(
        cls,
        content: AsyncIterable[bytes],
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None
    ) -> "Response":
        """Создать потоковый ответ"""
        return cls(content, status_code, headers)
        
    async def __call__(self, send: Any) -> None:
        """Send the response through ASGI interface"""
        headers = self.headers_list
        
        await send({
            "type": "http.response.start",
            "status": self.status,
            "headers": headers
        })
        
        body = await self.body
        await send({
            "type": "http.response.body",
            "body": body
        })
        
class JSONResponse(Response):
    def __init__(
        self,
        content: dict,
        status_code: int = 200,
        headers: Optional[List[Tuple[bytes, bytes]]] = None
    ):
        super().__init__(content, status_code, headers)
        
class HTMLResponse(Response):
    def __init__(
        self,
        content: str,
        status_code: int = 200,
        headers: Optional[List[Tuple[bytes, bytes]]] = None
    ):
        super().__init__(content, status_code, headers)
        
class PlainTextResponse(Response):
    def __init__(
        self,
        content: str,
        status_code: int = 200,
        headers: Optional[List[Tuple[bytes, bytes]]] = None
    ):
        super().__init__(content, status_code, headers)
        
class RedirectResponse(Response):
    def __init__(
        self,
        url: str,
        status_code: int = 307,
        headers: Optional[List[Tuple[bytes, bytes]]] = None
    ):
        headers = headers or []
        headers.append((b"location", url.encode()))
        super().__init__(b"", status_code, headers) 