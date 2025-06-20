import secrets
from typing import List, Optional, Callable
from ..core.requests import Request
from ..core.responses import Response

class CSRFMiddleware:
    def __init__(
        self,
        secret_key: str,
        safe_methods: List[str] = ["GET", "HEAD", "OPTIONS"],
        token_field_name: str = "csrf_token",
        cookie_name: str = "csrf_token",
        cookie_secure: bool = True,
        cookie_httponly: bool = True,
        cookie_samesite: str = "Lax",
    ):
        self.secret_key = secret_key
        self.safe_methods = safe_methods
        self.token_field_name = token_field_name
        self.cookie_name = cookie_name
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite

    async def __call__(self, request: Request, handler: Callable) -> Response:
        if request.method in self.safe_methods:
            response = await handler(request)
            return self._set_csrf_cookie(response)

        token = self._get_token_from_request(request)
        cookie_token = self._get_token_from_cookie(request)

        if not token or not cookie_token:
            return Response.json(
                {"detail": "CSRF token missing or invalid"},
                status_code=403,
                headers=[(b"content-type", b"application/json")]
            )

        if isinstance(cookie_token, str):
            cookie_value = cookie_token
        else:
            cookie_value = cookie_token.value

        if token != cookie_value:
            return Response.json(
                {"detail": "CSRF token missing or invalid"},
                status_code=403,
                headers=[(b"content-type", b"application/json")]
            )

        response = await handler(request)
        return self._set_csrf_cookie(response)

    def _generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def _get_token_from_request(self, request: Request) -> Optional[str]:
        # Проверяем токен в заголовке X-CSRF-Token
        token = request.headers.get(b"x-csrf-token", b"").decode()
        if token:
            return token

        # Проверяем токен в теле запроса
        try:
            body = request.json()
            return body.get(self.token_field_name)
        except:
            return None

    def _get_token_from_cookie(self, request: Request) -> Optional[str]:
        return request.cookies.get(self.cookie_name)

    def _set_csrf_cookie(self, response: Response) -> Response:
        token = self._generate_token()
        cookie_value = f"{self.cookie_name}={token}; Path=/; SameSite={self.cookie_samesite}"
        
        if self.cookie_httponly:
            cookie_value += "; HttpOnly"
        
        if self.cookie_secure:
            cookie_value += "; Secure"
        
        response.headers.extend([
            (b"set-cookie", cookie_value.encode()),
            (b"x-csrf-token", token.encode())
        ])
        return response 