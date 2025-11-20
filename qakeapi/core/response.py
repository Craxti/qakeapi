"""
Модуль for HTTP responseоin
"""
import json
import os
from typing import Any, Dict, Optional, Union, AsyncGenerator
from urllib.parse import quote

from ..utils.status import status


class Response:
    """Базоinый класс for HTTP responseоin"""
    
    def __init__(
        self,
        content: Any = None,
        status_code: int = status.OK,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
    ) -> None:
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}
        self.media_type = media_type
        self.cookies: Dict[str, Dict[str, Any]] = {}
        self._body: Optional[bytes] = None
        
        if media_type is not None:
            self.headers["content-type"] = media_type
    
    def get_header(self, name: str) -> Optional[str]:
        """Получandть заголоinок по andменand"""
        return self.headers.get(name.lower())
    
    def set_header(self, name: str, value: str) -> None:
        """Устаноinandть заголоinок"""
        self.headers[name.lower()] = value
    
    @property
    def body(self) -> bytes:
        """Получandть body responseа in inandде bytes"""
        if self._body is not None:
            return self._body
        
        if self.content is None:
            return b""
        
        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, str):
            return self.content.encode('utf-8')
        else:
            return str(self.content).encode('utf-8')
    
    def set_cookie(
        self,
        key: str,
        value: str = "",
        max_age: Optional[int] = None,
        expires: Optional[str] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Optional[str] = None,
    ) -> None:
        """Устаноinandть cookie"""
        self.cookies[key] = {
            "value": value,
            "max_age": max_age,
            "expires": expires,
            "path": path,
            "domain": domain,
            "secure": secure,
            "httponly": httponly,
            "samesite": samesite,
        }
    
    def delete_cookie(
        self,
        key: str,
        path: str = "/",
        domain: Optional[str] = None,
    ) -> None:
        """Удалandть cookie"""
        self.set_cookie(
            key=key,
            value="",
            max_age=0,
            path=path,
            domain=domain,
        )
    
    def _build_cookie_header(self, key: str, cookie_data: Dict[str, Any]) -> str:
        """Построandть заголоinок Set-Cookie"""
        cookie_parts = [f"{key}={quote(str(cookie_data['value']))}"]
        
        if cookie_data.get("max_age") is not None:
            cookie_parts.append(f"Max-Age={cookie_data['max_age']}")
        
        if cookie_data.get("expires"):
            cookie_parts.append(f"Expires={cookie_data['expires']}")
        
        if cookie_data.get("path"):
            cookie_parts.append(f"Path={cookie_data['path']}")
        
        if cookie_data.get("domain"):
            cookie_parts.append(f"Domain={cookie_data['domain']}")
        
        if cookie_data.get("secure"):
            cookie_parts.append("Secure")
        
        if cookie_data.get("httponly"):
            cookie_parts.append("HttpOnly")
        
        if cookie_data.get("samesite"):
            cookie_parts.append(f"SameSite={cookie_data['samesite']}")
        
        return "; ".join(cookie_parts)
    
    async def __call__(self, scope: Dict[str, Any], receive: callable, send: callable) -> None:
        """ASGI andнтерфейс"""
        # Добаinляем cookies in headers
        if self.cookies:
            cookie_headers = []
            for key, cookie_data in self.cookies.items():
                cookie_headers.append(self._build_cookie_header(key, cookie_data))
            
            if "set-cookie" in self.headers:
                if isinstance(self.headers["set-cookie"], list):
                    self.headers["set-cookie"].extend(cookie_headers)
                else:
                    self.headers["set-cookie"] = [self.headers["set-cookie"]] + cookie_headers
            else:
                self.headers["set-cookie"] = cookie_headers
        
        # Подготаinлandinаем headers for ASGI
        headers = []
        for name, value in self.headers.items():
            if isinstance(value, list):
                for v in value:
                    headers.append([name.encode(), v.encode()])
            else:
                headers.append([name.encode(), value.encode()])
        
        # Отpermissionsляем начало responseа
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": headers,
        })
        
        # Отpermissionsляем body responseа
        if self.content is not None:
            if isinstance(self.content, (str, bytes)):
                body = self.content.encode() if isinstance(self.content, str) else self.content
                await send({
                    "type": "http.response.body",
                    "body": body,
                })
            elif hasattr(self.content, "__aiter__"):
                # Асandнхронный геnotратор
                async for chunk in self.content:
                    chunk_bytes = chunk.encode() if isinstance(chunk, str) else chunk
                    await send({
                        "type": "http.response.body",
                        "body": chunk_bytes,
                        "more_body": True,
                    })
                await send({
                    "type": "http.response.body",
                    "body": b"",
                })
            else:
                # Другandе typeы данных
                body = str(self.content).encode()
                await send({
                    "type": "http.response.body",
                    "body": body,
                })
        else:
            await send({
                "type": "http.response.body",
                "body": b"",
            })


class JSONResponse(Response):
    """JSON response"""
    
    def __init__(
        self,
        content: Any = None,
        status_code: int = status.OK,
        headers: Optional[Dict[str, str]] = None,
        **json_kwargs: Any,
    ) -> None:
        self.json_kwargs = json_kwargs
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="application/json",
        )
    
    @property
    def body(self) -> bytes:
        """Получandть body responseа in inandде bytes"""
        if self._body is not None:
            return self._body
        
        if self.content is None:
            return b"{}"
        
        json_str = json.dumps(
            self.content,
            ensure_ascii=False,
            **self.json_kwargs
        )
        return json_str.encode('utf-8')
    
    async def __call__(self, scope: Dict[str, Any], receive: callable, send: callable) -> None:
        # Используем body property, который учandтыinает сжатandе
        if self._body is not None:
            # Данные уже обработаны (напрandмер, сжаты middleware)
            body_data = self._body
        elif self.content is not None:
            # Оleastчная JSON серandалandзацandя
            json_str = json.dumps(
                self.content,
                ensure_ascii=False,
                **self.json_kwargs
            )
            body_data = json_str.encode('utf-8')
        else:
            body_data = b"{}"
        
        # Отpermissionsляем headers
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": [
                (name.encode(), value.encode()) 
                for name, value in self.headers.items()
            ],
        })
        
        # Отpermissionsляем body
        await send({
            "type": "http.response.body",
            "body": body_data,
        })


class HTMLResponse(Response):
    """HTML response"""
    
    def __init__(
        self,
        content: str = "",
        status_code: int = status.OK,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="text/html; charset=utf-8",
        )


class PlainTextResponse(Response):
    """Текстоinый response"""
    
    def __init__(
        self,
        content: str = "",
        status_code: int = status.OK,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="text/plain; charset=utf-8",
        )


class RedirectResponse(Response):
    """Отinет с перенаpermissionsленandем"""
    
    def __init__(
        self,
        url: str,
        status_code: int = status.FOUND,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        headers = headers or {}
        headers["location"] = url
        super().__init__(
            content=None,
            status_code=status_code,
            headers=headers,
        )


class FileResponse(Response):
    """Отinет с файлом"""
    
    def __init__(
        self,
        path: str,
        status_code: int = status.OK,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> None:
        self.path = path
        self.filename = filename
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        if media_type is None:
            media_type = self._guess_media_type(path)
        
        headers = headers or {}
        if filename:
            headers["content-disposition"] = f'attachment; filename="{filename}"'
        
        # Устанаinлandinаем размер файла
        stat_result = os.stat(path)
        headers["content-length"] = str(stat_result.st_size)
        
        super().__init__(
            content=None,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
        )
    
    def _guess_media_type(self, path: str) -> str:
        """Определandть MIME type по расшandренandю файла"""
        ext = os.path.splitext(path)[1].lower()
        mime_types = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".xml": "application/xml",
            ".zip": "application/zip",
        }
        return mime_types.get(ext, "application/octet-stream")
    
    async def _file_generator(self, file_path: str, chunk_size: int = 8192) -> AsyncGenerator[bytes, None]:
        """Геnotратор for чтенandя файла по частям"""
        with open(file_path, "rb") as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    async def __call__(self, scope: Dict[str, Any], receive: callable, send: callable) -> None:
        # Подготаinлandinаем headers for ASGI
        headers = []
        for name, value in self.headers.items():
            headers.append([name.encode(), value.encode()])
        
        # Отpermissionsляем начало responseа
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": headers,
        })
        
        # Отpermissionsляем файл по частям
        async for chunk in self._file_generator(self.path):
            await send({
                "type": "http.response.body",
                "body": chunk,
                "more_body": True,
            })
        
        await send({
            "type": "http.response.body",
            "body": b"",
        })


class StreamingResponse(Response):
    """Потокоinый response"""
    
    def __init__(
        self,
        content: AsyncGenerator[bytes, None],
        status_code: int = status.OK,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
    ) -> None:
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
        )
