"""
Tests for WebSocket Authentication System.

Tests cover all authentication scenarios and edge cases.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from qakeapi.security.websocket_auth import (
    AuthStatus,
    AuthResult,
    AuthConfig,
    WebSocketAuthenticator,
    JWTAuthenticator,
    WebSocketAuthMiddleware,
    WebSocketAuthHandler,
    AuthenticatorFactory,
)
from qakeapi.core.websockets import WebSocketConnection


class TestAuthStatus:
    """Test authentication status enumeration."""

    def test_auth_status_values(self):
        """Test that all auth status values are defined."""
        assert AuthStatus.PENDING.value == "pending"
        assert AuthStatus.AUTHENTICATED.value == "authenticated"
        assert AuthStatus.UNAUTHENTICATED.value == "unauthenticated"
        assert AuthStatus.EXPIRED.value == "expired"
        assert AuthStatus.INVALID.value == "invalid"


class TestAuthResult:
    """Test authentication result data class."""

    def test_auth_result_creation(self):
        """Test creating AuthResult with all fields."""
        result = AuthResult(
            status=AuthStatus.AUTHENTICATED,
            user_id="user123",
            user_data={"name": "Test User"},
            expires_at=datetime.now(),
            metadata={"ip": "127.0.0.1"},
        )

        assert result.status == AuthStatus.AUTHENTICATED
        assert result.user_id == "user123"
        assert result.user_data["name"] == "Test User"
        assert result.metadata["ip"] == "127.0.0.1"

    def test_auth_result_minimal(self):
        """Test creating AuthResult with minimal fields."""
        result = AuthResult(status=AuthStatus.UNAUTHENTICATED)

        assert result.status == AuthStatus.UNAUTHENTICATED
        assert result.user_id is None
        assert result.user_data is None
        assert result.error_message is None
        assert result.metadata == {}


class TestAuthConfig:
    """Test authentication configuration."""

    def test_auth_config_defaults(self):
        """Test AuthConfig with default values."""
        config = AuthConfig(secret_key="test_secret")

        assert config.secret_key == "test_secret"
        assert config.algorithm == "HS256"
        assert config.max_auth_attempts == 3
        assert config.auth_timeout == 30.0
        assert config.require_auth is True
        assert config.allow_anonymous is False

    def test_auth_config_custom(self):
        """Test AuthConfig with custom values."""
        config = AuthConfig(
            secret_key="custom_secret",
            algorithm="HS512",
            token_expiry=timedelta(hours=2),
            max_auth_attempts=5,
            auth_timeout=60.0,
            require_auth=False,
            allow_anonymous=True,
        )

        assert config.secret_key == "custom_secret"
        assert config.algorithm == "HS512"
        assert config.max_auth_attempts == 5
        assert config.auth_timeout == 60.0
        assert config.require_auth is False
        assert config.allow_anonymous is True


class TestJWTAuthenticator:
    """Test JWT-based authenticator."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AuthConfig(secret_key="test_secret_key_12345")

    @pytest.fixture
    def authenticator(self, config):
        """Create JWT authenticator."""
        return JWTAuthenticator(config)

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection."""
        websocket = Mock(spec=WebSocketConnection)
        websocket.connection_id = "test_connection_123"
        return websocket

    @pytest.mark.asyncio
    async def test_create_token(self, authenticator):
        """Test token creation."""
        user_data = {
            "user_id": "user123",
            "name": "Test User",
            "email": "test@example.com",
        }

        token = await authenticator.create_token(user_data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token can be decoded
        result = await authenticator.validate_token(token)
        assert result.status == AuthStatus.AUTHENTICATED
        assert result.user_id == "user123"
        assert result.user_data["name"] == "Test User"

    @pytest.mark.asyncio
    async def test_validate_token_success(self, authenticator):
        """Test successful token validation."""
        user_data = {"user_id": "user123", "name": "Test User"}
        token = await authenticator.create_token(user_data)

        result = await authenticator.validate_token(token)

        assert result.status == AuthStatus.AUTHENTICATED
        assert result.user_id == "user123"
        assert result.user_data["name"] == "Test User"

    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, authenticator):
        """Test invalid token validation."""
        result = await authenticator.validate_token("invalid_token")

        assert result.status == AuthStatus.INVALID
        assert "Invalid token" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_token_expired(self, authenticator):
        """Test expired token validation."""
        # Create token with short expiry
        config = AuthConfig(
            secret_key="test_secret_key_12345", token_expiry=timedelta(seconds=1)
        )
        short_authenticator = JWTAuthenticator(config)

        user_data = {"user_id": "user123"}
        token = await short_authenticator.create_token(user_data)

        # Wait for token to expire
        await asyncio.sleep(1.1)

        result = await short_authenticator.validate_token(token)

        assert result.status == AuthStatus.EXPIRED
        assert "expired" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_revoke_token(self, authenticator):
        """Test token revocation."""
        user_data = {"user_id": "user123"}
        token = await authenticator.create_token(user_data)

        # Token should be valid initially
        result = await authenticator.validate_token(token)
        assert result.status == AuthStatus.AUTHENTICATED

        # Revoke token
        success = await authenticator.revoke_token(token)
        assert success is True

        # Token should be invalid after revocation
        result = await authenticator.validate_token(token)
        assert result.status == AuthStatus.INVALID
        assert "revoked" in result.error_message

    @pytest.mark.asyncio
    async def test_authenticate_success(self, authenticator, mock_websocket):
        """Test successful authentication."""
        user_data = {"user_id": "user123", "name": "Test User"}
        token = await authenticator.create_token(user_data)

        auth_data = {"token": token}
        result = await authenticator.authenticate(mock_websocket, auth_data)

        assert result.status == AuthStatus.AUTHENTICATED
        assert result.user_id == "user123"
        assert authenticator._auth_attempts[mock_websocket.connection_id] == 0

    @pytest.mark.asyncio
    async def test_authenticate_no_token(self, authenticator, mock_websocket):
        """Test authentication without token."""
        auth_data = {}
        result = await authenticator.authenticate(mock_websocket, auth_data)

        assert result.status == AuthStatus.UNAUTHENTICATED
        assert "No token provided" in result.error_message

    @pytest.mark.asyncio
    async def test_authenticate_revoked_token(self, authenticator, mock_websocket):
        """Test authentication with revoked token."""
        user_data = {"user_id": "user123"}
        token = await authenticator.create_token(user_data)

        # Revoke token
        await authenticator.revoke_token(token)

        auth_data = {"token": token}
        result = await authenticator.authenticate(mock_websocket, auth_data)

        assert result.status == AuthStatus.INVALID
        assert "revoked" in result.error_message


class TestWebSocketAuthMiddleware:
    """Test WebSocket authentication middleware."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AuthConfig(secret_key="test_secret_key_12345")

    @pytest.fixture
    def authenticator(self, config):
        """Create JWT authenticator."""
        return JWTAuthenticator(config)

    @pytest.fixture
    def middleware(self, authenticator, config):
        """Create authentication middleware."""
        return WebSocketAuthMiddleware(authenticator, config)

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection."""
        websocket = Mock(spec=WebSocketConnection)
        websocket.connection_id = "test_connection_123"
        websocket.receive_json = AsyncMock()
        websocket.send_json = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_authenticate_connection_success(self, middleware, mock_websocket):
        """Test successful connection authentication."""
        user_data = {"user_id": "user123", "name": "Test User"}
        token = await middleware.authenticator.create_token(user_data)

        # Mock authentication message
        auth_message = {"type": "auth", "data": {"token": token}}
        mock_websocket.receive_json.return_value = auth_message

        result = await middleware.authenticate_connection(mock_websocket)

        assert result.status == AuthStatus.AUTHENTICATED
        assert middleware.is_authenticated(mock_websocket.connection_id)

        # Verify success message was sent
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "auth_success"
        assert call_args["data"]["user_id"] == "user123"

    @pytest.mark.asyncio
    async def test_authenticate_connection_wrong_message_type(
        self, middleware, mock_websocket
    ):
        """Test authentication with wrong message type."""
        # Mock wrong message type
        wrong_message = {"type": "chat", "data": {"message": "Hello"}}
        mock_websocket.receive_json.return_value = wrong_message

        result = await middleware.authenticate_connection(mock_websocket)

        assert result.status == AuthStatus.UNAUTHENTICATED
        assert "Authentication message expected" in result.error_message
        assert not middleware.is_authenticated(mock_websocket.connection_id)

    @pytest.mark.asyncio
    async def test_authenticate_connection_timeout(self, middleware, mock_websocket):
        """Test authentication timeout."""
        # Mock timeout
        mock_websocket.receive_json.side_effect = asyncio.TimeoutError()

        result = await middleware.authenticate_connection(mock_websocket)

        assert result.status == AuthStatus.UNAUTHENTICATED
        assert "timeout" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_authenticate_connection_max_attempts(
        self, middleware, mock_websocket
    ):
        """Test maximum authentication attempts."""
        # Set up max attempts
        middleware._auth_attempts[
            mock_websocket.connection_id
        ] = middleware.config.max_auth_attempts

        result = await middleware.authenticate_connection(mock_websocket)

        assert result.status == AuthStatus.INVALID
        assert "Too many authentication attempts" in result.error_message

    def test_is_authenticated(self, middleware):
        """Test authentication status check."""
        connection_id = "test_connection"

        # Initially not authenticated
        assert not middleware.is_authenticated(connection_id)

        # Add to authenticated connections
        auth_result = AuthResult(status=AuthStatus.AUTHENTICATED, user_id="user123")
        middleware._authenticated_connections[connection_id] = auth_result

        assert middleware.is_authenticated(connection_id)

    def test_get_auth_data(self, middleware):
        """Test getting authentication data."""
        connection_id = "test_connection"
        auth_result = AuthResult(status=AuthStatus.AUTHENTICATED, user_id="user123")
        middleware._authenticated_connections[connection_id] = auth_result

        result = middleware.get_auth_data(connection_id)
        assert result == auth_result

        # Test non-existent connection
        assert middleware.get_auth_data("non_existent") is None

    def test_remove_connection(self, middleware):
        """Test removing connection."""
        connection_id = "test_connection"

        # Add connection
        auth_result = AuthResult(status=AuthStatus.AUTHENTICATED, user_id="user123")
        middleware._authenticated_connections[connection_id] = auth_result
        middleware._auth_attempts[connection_id] = 2

        # Remove connection
        middleware.remove_connection(connection_id)

        assert not middleware.is_authenticated(connection_id)
        assert middleware.get_auth_data(connection_id) is None
        assert connection_id not in middleware._auth_attempts


class TestWebSocketAuthHandler:
    """Test WebSocket authentication handler."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AuthConfig(secret_key="test_secret_key_12345")

    @pytest.fixture
    def authenticator(self, config):
        """Create JWT authenticator."""
        return JWTAuthenticator(config)

    @pytest.fixture
    def middleware(self, authenticator, config):
        """Create authentication middleware."""
        return WebSocketAuthMiddleware(authenticator, config)

    @pytest.fixture
    def handler(self, middleware):
        """Create authentication handler."""
        return WebSocketAuthHandler(middleware)

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection."""
        websocket = Mock(spec=WebSocketConnection)
        websocket.connection_id = "test_connection_123"
        websocket.send_json = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_require_auth_authenticated(
        self, handler, mock_websocket, middleware
    ):
        """Test require_auth decorator with authenticated user."""
        # Add to authenticated connections
        auth_result = AuthResult(status=AuthStatus.AUTHENTICATED, user_id="user123")
        middleware._authenticated_connections[mock_websocket.connection_id] = (
            auth_result
        )

        # Create test handler
        @handler.require_auth
        async def test_handler(websocket, message):
            return "success"

        message = {"type": "test", "data": {}}
        result = await test_handler(mock_websocket, message)

        assert result == "success"
        mock_websocket.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_require_auth_unauthenticated(self, handler, mock_websocket):
        """Test require_auth decorator with unauthenticated user."""

        # Create test handler
        @handler.require_auth
        async def test_handler(websocket, message):
            return "success"

        message = {"type": "test", "data": {}}
        result = await test_handler(mock_websocket, message)

        assert result is None
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["data"]["code"] == "AUTH_REQUIRED"

    @pytest.mark.asyncio
    async def test_optional_auth_authenticated(
        self, handler, mock_websocket, middleware
    ):
        """Test optional_auth decorator with authenticated user."""
        # Add to authenticated connections
        auth_result = AuthResult(status=AuthStatus.AUTHENTICATED, user_id="user123")
        middleware._authenticated_connections[mock_websocket.connection_id] = (
            auth_result
        )

        # Create test handler
        @handler.optional_auth
        async def test_handler(websocket, message):
            return message.get("auth")

        message = {"type": "test", "data": {}}
        result = await test_handler(mock_websocket, message)

        assert result["user_id"] == "user123"

    @pytest.mark.asyncio
    async def test_optional_auth_unauthenticated(self, handler, mock_websocket):
        """Test optional_auth decorator with unauthenticated user."""

        # Create test handler
        @handler.optional_auth
        async def test_handler(websocket, message):
            return message.get("auth")

        message = {"type": "test", "data": {}}
        result = await test_handler(mock_websocket, message)

        assert result is None


class TestAuthenticatorFactory:
    """Test authenticator factory."""

    def test_create_jwt_authenticator(self):
        """Test creating JWT authenticator."""
        config = AuthConfig(secret_key="test_secret")
        authenticator = AuthenticatorFactory.create_jwt_authenticator(config)

        assert isinstance(authenticator, JWTAuthenticator)
        assert authenticator.config == config

    def test_create_auth_middleware(self):
        """Test creating authentication middleware."""
        config = AuthConfig(secret_key="test_secret")
        authenticator = JWTAuthenticator(config)
        middleware = AuthenticatorFactory.create_auth_middleware(authenticator, config)

        assert isinstance(middleware, WebSocketAuthMiddleware)
        assert middleware.authenticator == authenticator
        assert middleware.config == config

    def test_create_auth_handler(self):
        """Test creating authentication handler."""
        config = AuthConfig(secret_key="test_secret")
        authenticator = JWTAuthenticator(config)
        middleware = WebSocketAuthMiddleware(authenticator, config)
        handler = AuthenticatorFactory.create_auth_handler(middleware)

        assert isinstance(handler, WebSocketAuthHandler)
        assert handler.middleware == middleware


class TestIntegration:
    """Integration tests for WebSocket authentication."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AuthConfig(
            secret_key="integration_test_secret_key_12345",
            token_expiry=timedelta(minutes=5),
            max_auth_attempts=3,
            auth_timeout=10.0,
        )

    @pytest.fixture
    def authenticator(self, config):
        """Create JWT authenticator."""
        return JWTAuthenticator(config)

    @pytest.fixture
    def middleware(self, authenticator, config):
        """Create authentication middleware."""
        return WebSocketAuthMiddleware(authenticator, config)

    @pytest.mark.asyncio
    async def test_full_authentication_flow(self, middleware, authenticator):
        """Test complete authentication flow."""
        # Create mock WebSocket
        websocket = Mock(spec=WebSocketConnection)
        websocket.connection_id = "integration_test_123"
        websocket.receive_json = AsyncMock()
        websocket.send_json = AsyncMock()

        # Create user data and token
        user_data = {
            "user_id": "integration_user",
            "name": "Integration Test User",
            "email": "integration@test.com",
        }
        token = await authenticator.create_token(user_data)

        # Mock authentication message
        auth_message = {"type": "auth", "data": {"token": token}}
        websocket.receive_json.return_value = auth_message

        # Perform authentication
        result = await middleware.authenticate_connection(websocket)

        # Verify results
        assert result.status == AuthStatus.AUTHENTICATED
        assert result.user_id == "integration_user"
        assert middleware.is_authenticated(websocket.connection_id)

        # Verify success message
        websocket.send_json.assert_called_once()
        call_args = websocket.send_json.call_args[0][0]
        assert call_args["type"] == "auth_success"
        assert call_args["data"]["user_id"] == "integration_user"

    @pytest.mark.asyncio
    async def test_authentication_with_revocation(self, middleware, authenticator):
        """Test authentication with token revocation."""
        # Create mock WebSocket
        websocket = Mock(spec=WebSocketConnection)
        websocket.connection_id = "revocation_test_123"
        websocket.receive_json = AsyncMock()
        websocket.send_json = AsyncMock()

        # Create and revoke token
        user_data = {"user_id": "revoked_user"}
        token = await authenticator.create_token(user_data)
        await authenticator.revoke_token(token)

        # Mock authentication message
        auth_message = {"type": "auth", "data": {"token": token}}
        websocket.receive_json.return_value = auth_message

        # Perform authentication
        result = await middleware.authenticate_connection(websocket)

        # Verify failure
        assert result.status == AuthStatus.INVALID
        assert "revoked" in result.error_message
        assert not middleware.is_authenticated(websocket.connection_id)

        # Verify error message
        websocket.send_json.assert_called_once()
        call_args = websocket.send_json.call_args[0][0]
        assert call_args["type"] == "auth_error"
        assert call_args["data"]["status"] == "invalid"
