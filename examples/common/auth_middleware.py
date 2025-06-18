import base64
import logging
from typing import Optional, Callable, Any
from functools import partial

from qakeapi.core.requests import Request
from qakeapi.core.responses import Response
from qakeapi.security.authentication import AuthenticationBackend, AuthenticationError

logger = logging.getLogger(__name__)

def create_auth_middleware(auth_backend: AuthenticationBackend, public_paths: list[str] = None, auth_header_prefix: str = "Bearer"):
    """
    Создает middleware для аутентификации
    
    Args:
        auth_backend: Бэкенд аутентификации
        public_paths: Список публичных путей, не требующих аутентификации
        auth_header_prefix: Префикс заголовка аутентификации (Bearer или Basic)
    """
    async def auth_middleware(request: Request, handler: Callable) -> Callable:
        logger.debug(f"Processing request: {request.method} {request.path}")
        logger.debug(f"Headers: {request.headers}")

        # Initialize user attribute
        request.user = None

        if public_paths and request.path in public_paths:
            logger.debug("Allowing access to public endpoint")
            return handler

        auth = None
        for header in request.scope["headers"]:
            if header[0].lower() == b"authorization":
                auth = header[1].decode()
                break

        logger.debug(f"Auth header: {auth}")

        if not auth:
            logger.debug("No auth header found")
            async def unauthorized_handler(request: Request) -> Response:
                response = Response.json({"detail": "Unauthorized"}, status_code=401)
                response.headers.extend([(b"WWW-Authenticate", b"Basic")])
                return response
            return unauthorized_handler

        try:
            if auth_header_prefix == "Basic":
                # Проверяем, начинается ли заголовок с "Basic "
                if not auth.startswith("Basic "):
                    logger.debug("Invalid Basic auth header format")
                    async def invalid_auth_handler(request: Request) -> Response:
                        return Response.json({"detail": "Invalid auth header"}, status_code=401)
                    return invalid_auth_handler

                # Декодируем Base64 credentials
                credentials_base64 = auth[6:]  # Пропускаем "Basic "
                logger.debug(f"Base64 credentials: {credentials_base64}")
                credentials_bytes = base64.b64decode(credentials_base64)
                credentials_str = credentials_bytes.decode('utf-8')
                logger.debug(f"Decoded credentials: {credentials_str}")
                username, password = credentials_str.split(':')
                credentials = {"username": username, "password": password}
                logger.debug(f"Extracted credentials: {credentials}")
            else:
                if not auth.startswith(f"{auth_header_prefix} "):
                    logger.debug(f"Invalid {auth_header_prefix} auth header format")
                    async def invalid_auth_handler(request: Request) -> Response:
                        return Response.json({"detail": "Invalid auth header"}, status_code=401)
                    return invalid_auth_handler
                credentials = {"token": auth[len(auth_header_prefix) + 1:]}
            
            user = await auth_backend.authenticate(credentials)
            logger.debug(f"Authentication result: {user}")
            
            if not user:
                logger.debug("Authentication failed")
                async def invalid_credentials_handler(request: Request) -> Response:
                    return Response.json({"detail": "Invalid credentials"}, status_code=401)
                return invalid_credentials_handler

            logger.debug(f"User authenticated: {user.username}")
            request.user = user

            async def authenticated_handler(request: Request) -> Response:
                try:
                    response = await handler(request)
                    logger.debug(f"Handler response: {response}")
                    if isinstance(response, Response):
                        return response
                    return Response.json(response)
                except Exception as e:
                    logger.error(f"Error in handler: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    return Response.json({"detail": "Internal server error"}, status_code=500)

            return authenticated_handler

        except AuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            async def auth_error_handler(request: Request) -> Response:
                return Response.json({"detail": str(e)}, status_code=401)
            return auth_error_handler
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            import traceback
            logger.error(traceback.format_exc())
            async def server_error_handler(request: Request) -> Response:
                return Response.json({"detail": "Internal server error"}, status_code=500)
            return server_error_handler

    return auth_middleware 