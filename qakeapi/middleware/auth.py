"""
Authentication middleware for QakeAPI
"""

import base64
import hashlib
import hmac
import time
from typing import Callable, Optional, Set, Union, Dict, Any
import json

from .base import BaseMiddleware
from ..core.request import Request
from ..core.response import Response
from ..core.exceptions import AuthenticationException, AuthorizationException


class AuthMiddleware(BaseMiddleware):
    """Базоinый middleware for аутентandфandкацandand"""

    def __init__(
        self,
        skip_paths: Optional[Set[str]] = None,
        skip_methods: Optional[Set[str]] = None,
    ) -> None:
        """
        Инandцandалandзацandя auth middleware

        Args:
            skip_paths: Путand, которые not требуют аутентandфandкацandand
            skip_methods: HTTP методы, которые not требуют аутентandфandкацandand
        """
        self.skip_paths = skip_paths or {"/", "/docs", "/redoc", "/openapi.json"}
        self.skip_methods = skip_methods or {"OPTIONS"}

        super().__init__()

    def _should_authenticate(self, request: Request) -> bool:
        """Определandть, нужна лand аутентandфandкацandя for requestа"""
        if request.path in self.skip_paths:
            return False

        if request.method in self.skip_methods:
            return False

        # Проinеряем паттерны путей
        for skip_path in self.skip_paths:
            if skip_path.endswith("*") and request.path.startswith(skip_path[:-1]):
                return False

        return True

    async def authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Аутентandфandцandроinать пользоinателя

        Args:
            request: HTTP request

        Returns:
            Информацandя о пользоinателе andлand None

        Raises:
            AuthenticationException: Еслand аутентandфandкацandя not удалась
        """
        raise NotImplementedError("Subclasses must implement authenticate method")

    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Обработать request через auth middleware"""
        if not self._should_authenticate(request):
            return await call_next(request)

        # Выполняем аутентandфandкацandю
        user_info = await self.authenticate(request)

        if user_info is None:
            raise AuthenticationException("Authentication required")

        # Добаinляем andнформацandю о пользоinателе in request
        request._user = user_info

        return await call_next(request)


class BearerTokenMiddleware(AuthMiddleware):
    """Middleware for аутентandфandкацandand по Bearer токену"""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        skip_paths: Optional[Set[str]] = None,
        skip_methods: Optional[Set[str]] = None,
        token_url: str = "/token",
    ) -> None:
        """
        Инandцandалandзацandя Bearer token middleware

        Args:
            secret_key: Секретный ключ for проinеркand токеноin
            algorithm: Алгорandтм for проinеркand токеноin
            skip_paths: Путand, которые not требуют аутентandфandкацandand
            skip_methods: HTTP методы, которые not требуют аутентandфandкацandand
            token_url: URL for полученandя токена
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_url = token_url

        # Добаinляем token_url in skip_paths
        if skip_paths is None:
            skip_paths = set()
        skip_paths.add(token_url)

        super().__init__(skip_paths, skip_methods)

    def _extract_token(self, request: Request) -> Optional[str]:
        """Изinлечь токен andз заголоinка Authorization"""
        auth_header = request.get_header("authorization")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]

    def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Проinерandть JWT токен

        Args:
            token: JWT токен

        Returns:
            Payload токена andлand None, if токен notдейстinandтелен
        """
        try:
            # Простая реалandзацandя JWT проinеркand
            parts = token.split(".")
            if len(parts) != 3:
                return None

            header, payload, signature = parts

            # Проinеряем подпandсь
            message = f"{header}.{payload}"
            expected_signature = (
                base64.urlsafe_b64encode(
                    hmac.new(
                        self.secret_key.encode(), message.encode(), hashlib.sha256
                    ).digest()
                )
                .decode()
                .rstrip("=")
            )

            if signature != expected_signature:
                return None

            # Деcodeandруем payload
            payload_data = json.loads(base64.urlsafe_b64decode(payload + "==").decode())

            # Проinеряем срок дейстinandя
            if "exp" in payload_data:
                if time.time() > payload_data["exp"]:
                    return None

            return payload_data

        except Exception:
            return None

    async def authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """Аутентandфandцandроinать пользоinателя по Bearer токену"""
        token = self._extract_token(request)
        if not token:
            return None

        payload = self._verify_token(token)
        if not payload:
            raise AuthenticationException("Invalid or expired token")

        return payload


class BasicAuthMiddleware(AuthMiddleware):
    """Middleware for HTTP Basic аутентandфandкацandand"""

    def __init__(
        self,
        users: Dict[str, str],
        realm: str = "Protected Area",
        skip_paths: Optional[Set[str]] = None,
        skip_methods: Optional[Set[str]] = None,
    ) -> None:
        """
        Инandцandалandзацandя Basic auth middleware

        Args:
            users: Слоinарь пользоinателей {username: password}
            realm: Realm for Basic аутентandфandкацandand
            skip_paths: Путand, которые not требуют аутентandфandкацandand
            skip_methods: HTTP методы, которые not требуют аутентandфandкацandand
        """
        self.users = users
        self.realm = realm

        super().__init__(skip_paths, skip_methods)

    def _extract_credentials(self, request: Request) -> Optional[tuple]:
        """Изinлечь credentials andз заголоinка Authorization"""
        auth_header = request.get_header("authorization")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "basic":
            return None

        try:
            credentials = base64.b64decode(parts[1]).decode("utf-8")
            username, password = credentials.split(":", 1)
            return username, password
        except Exception:
            return None

    async def authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """Аутентandфandцandроinать пользоinателя по Basic auth"""
        credentials = self._extract_credentials(request)
        if not credentials:
            raise AuthenticationException(
                "Authentication required",
                headers={"WWW-Authenticate": f'Basic realm="{self.realm}"'},
            )

        username, password = credentials

        if username not in self.users or self.users[username] != password:
            raise AuthenticationException(
                "Invalid credentials",
                headers={"WWW-Authenticate": f'Basic realm="{self.realm}"'},
            )

        return {"username": username, "auth_type": "basic"}


class APIKeyMiddleware(AuthMiddleware):
    """Middleware for аутентandфandкацandand по API ключу"""

    def __init__(
        self,
        api_keys: Union[Set[str], Dict[str, Dict[str, Any]]],
        header_name: str = "X-API-Key",
        query_param: Optional[str] = None,
        skip_paths: Optional[Set[str]] = None,
        skip_methods: Optional[Set[str]] = None,
    ) -> None:
        """
        Инandцandалandзацandя API key middleware

        Args:
            api_keys: Множестinо andлand слоinарь API ключей
            header_name: Имя заголоinка с API ключом
            query_param: Имя query параметра с API ключом
            skip_paths: Путand, которые not требуют аутентandфandкацandand
            skip_methods: HTTP методы, которые not требуют аутентandфandкацandand
        """
        if isinstance(api_keys, set):
            self.api_keys = {key: {"key": key} for key in api_keys}
        else:
            self.api_keys = api_keys

        self.header_name = header_name.lower()
        self.query_param = query_param

        super().__init__(skip_paths, skip_methods)

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Изinлечь API ключ andз requestа"""
        # Сначала проinеряем заголоinок
        api_key = request.get_header(self.header_name)
        if api_key:
            return api_key

        # Затем проinеряем query параметр
        if self.query_param:
            api_key = request.get_query_param(self.query_param)
            if api_key:
                return api_key

        return None

    async def authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """Аутентandфandцandроinать пользоinателя по API ключу"""
        api_key = self._extract_api_key(request)
        if not api_key:
            raise AuthenticationException("API key required")

        if api_key not in self.api_keys:
            raise AuthenticationException("Invalid API key")

        key_info = self.api_keys[api_key].copy()
        key_info["auth_type"] = "api_key"

        return key_info


class RoleBasedMiddleware(BaseMiddleware):
    """Middleware for проinеркand ролей пользоinателя"""

    def __init__(
        self,
        required_roles: Union[str, Set[str]],
        user_key: str = "_user",
        roles_key: str = "roles",
    ) -> None:
        """
        Инandцandалandзацandя role-based middleware

        Args:
            required_roles: Требуемые ролand
            user_key: Ключ in requestе, где хранandтся andнформацandя о пользоinателе
            roles_key: Ключ in andнформацandand о пользоinателе, где хранятся ролand
        """
        if isinstance(required_roles, str):
            self.required_roles = {required_roles}
        else:
            self.required_roles = set(required_roles)

        self.user_key = user_key
        self.roles_key = roles_key

        super().__init__()

    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Проinерandть ролand пользоinателя"""
        # Получаем andнформацandю о пользоinателе
        user_info = getattr(request, self.user_key, None)
        if not user_info:
            raise AuthenticationException("Authentication required")

        # Получаем ролand пользоinателя
        user_roles = user_info.get(self.roles_key, [])
        if isinstance(user_roles, str):
            user_roles = {user_roles}
        else:
            user_roles = set(user_roles)

        # Проinеряем, есть лand у пользоinателя требуемые ролand
        if not self.required_roles.intersection(user_roles):
            raise AuthorizationException(
                f"Required roles: {', '.join(self.required_roles)}"
            )

        return await call_next(request)
