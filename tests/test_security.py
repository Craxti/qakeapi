"""
Тесты системы безопасности
"""
import pytest
import asyncio
from unittest.mock import Mock, patch

from qakeapi.security.auth import JWTManager, PasswordManager, SecurityConfig
from qakeapi.security.rate_limiting import (
    RateLimiter,
    RateLimitRule,
    InMemoryRateLimiter,
)
from qakeapi.security.validation import SecurityValidator, ValidationConfig
from qakeapi.core.exceptions import HTTPException
from qakeapi.core.request import Request


class TestPasswordManager:
    """Тесты менеджера паролей"""

    def test_password_hashing(self):
        """Тест хеширования паролей"""
        config = SecurityConfig(password_min_length=6)
        manager = PasswordManager(config)

        password = "TestPassword123!"
        hashed = manager.hash_password(password)

        assert hashed != password
        assert manager.verify_password(password, hashed)
        assert not manager.verify_password("wrong_password", hashed)

    def test_password_strength_validation(self):
        """Тест валидации силы пароля"""
        config = SecurityConfig(
            password_min_length=8,
            password_require_uppercase=True,
            password_require_lowercase=True,
            password_require_digits=True,
            password_require_special=True,
        )
        manager = PasswordManager(config)

        # Слабые пароли должны вызывать исключения
        with pytest.raises(HTTPException):
            manager.validate_password_strength("weak")

        with pytest.raises(HTTPException):
            manager.validate_password_strength("nouppercase123!")

        with pytest.raises(HTTPException):
            manager.validate_password_strength("NOLOWERCASE123!")

        with pytest.raises(HTTPException):
            manager.validate_password_strength("NoDigits!")

        with pytest.raises(HTTPException):
            manager.validate_password_strength("NoSpecial123")

        # Сильный пароль должен проходить валидацию
        strong_password = "StrongPassword123!"
        manager.validate_password_strength(
            strong_password
        )  # Не должно вызывать исключение


class TestJWTManager:
    """Тесты менеджера JWT"""

    def test_token_creation_and_verification(self):
        """Тест создания и проверки токенов"""
        config = SecurityConfig(secret_key="test-secret-key")
        manager = JWTManager(config)

        data = {"user_id": 123, "username": "testuser"}

        # Создаем access токен
        access_token = manager.create_access_token(data)
        assert access_token is not None

        # Проверяем токен
        token_data = manager.verify_token(access_token, "access")
        assert token_data.user_id == 123
        assert token_data.username == "testuser"

    def test_token_pair_creation(self):
        """Тест создания пары токенов"""
        config = SecurityConfig(secret_key="test-secret-key")
        manager = JWTManager(config)

        data = {"user_id": 123, "username": "testuser"}
        token_pair = manager.create_token_pair(data)

        assert token_pair.access_token is not None
        assert token_pair.refresh_token is not None
        assert token_pair.token_type == "bearer"
        assert token_pair.expires_in > 0

    def test_refresh_token(self):
        """Тест обновления токена"""
        config = SecurityConfig(secret_key="test-secret-key")
        manager = JWTManager(config)

        data = {"user_id": 123, "username": "testuser"}
        token_pair = manager.create_token_pair(data)

        # Обновляем access токен
        new_access_token = manager.refresh_access_token(token_pair.refresh_token)
        assert new_access_token is not None

        # Проверяем новый токен
        token_data = manager.verify_token(new_access_token, "access")
        assert token_data.user_id == 123
        assert token_data.username == "testuser"

    def test_invalid_token(self):
        """Тест невалидного токена"""
        config = SecurityConfig(secret_key="test-secret-key")
        manager = JWTManager(config)

        with pytest.raises(HTTPException):
            manager.verify_token("invalid-token", "access")


class TestRateLimiter:
    """Тесты rate limiter"""

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Тест ограничения скорости"""
        backend = InMemoryRateLimiter()
        rule = RateLimitRule(requests=2, window=1)  # 2 запроса в секунду

        # Первые два запроса должны пройти
        allowed1, _ = await backend.is_allowed("test_key", rule)
        assert allowed1 is True

        allowed2, _ = await backend.is_allowed("test_key", rule)
        assert allowed2 is True

        # Третий запрос должен быть заблокирован
        allowed3, _ = await backend.is_allowed("test_key", rule)
        assert allowed3 is False

        # После ожидания должен снова разрешить
        await asyncio.sleep(1.1)
        allowed4, _ = await backend.is_allowed("test_key", rule)
        assert allowed4 is True

    @pytest.mark.asyncio
    async def test_rate_limiter_with_request(self):
        """Тест rate limiter с запросом"""
        limiter = RateLimiter()
        limiter.add_rule("/api/*", RateLimitRule(requests=1, window=1))

        # Создаем мок запроса
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "client": ("127.0.0.1", 12345),
            "headers": [],
        }
        request = Request(scope, None)

        # Первый запрос должен пройти
        allowed1, _, _ = await limiter.check_rate_limit(request)
        assert allowed1 is True

        # Второй запрос должен быть заблокирован
        allowed2, _, _ = await limiter.check_rate_limit(request)
        assert allowed2 is False


class TestSecurityValidator:
    """Тесты валидатора безопасности"""

    def test_string_sanitization(self):
        """Тест санитизации строк"""
        config = ValidationConfig(allow_html=False, sanitize_strings=True)
        validator = SecurityValidator(config)

        # Безопасный HTML должен быть экранирован
        safe_html = "<p>Hello World</p>"
        result = validator.sanitize_string(safe_html)
        assert "<p>" not in result
        assert "&lt;p&gt;" in result

    def test_dangerous_patterns_detection(self):
        """Тест обнаружения опасных паттернов"""
        validator = SecurityValidator()

        # SQL injection
        with pytest.raises(HTTPException):
            validator.sanitize_string("'; DROP TABLE users; --")

        # XSS
        with pytest.raises(HTTPException):
            validator.sanitize_string("<script>alert('xss')</script>")

        # Path traversal
        with pytest.raises(HTTPException):
            validator.sanitize_string("../../../etc/passwd")

    def test_dict_validation(self):
        """Тест валидации словарей"""
        validator = SecurityValidator()

        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "nested": {"value": "test"},
        }

        result = validator.validate_dict(data)
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"
        assert result["nested"]["value"] == "test"

    def test_list_validation(self):
        """Тест валидации списков"""
        validator = SecurityValidator()

        data = ["item1", "item2", {"key": "value"}]
        result = validator.validate_list(data)

        assert len(result) == 3
        assert result[0] == "item1"
        assert result[1] == "item2"
        assert result[2]["key"] == "value"

    def test_max_length_validation(self):
        """Тест валидации максимальной длины"""
        config = ValidationConfig(max_string_length=10)
        validator = SecurityValidator(config)

        # Короткая строка должна пройти
        short_string = "short"
        result = validator.sanitize_string(short_string)
        assert result == short_string

        # Длинная строка должна вызвать исключение
        long_string = "a" * 20
        with pytest.raises(HTTPException):
            validator.sanitize_string(long_string)

    def test_deep_nesting_validation(self):
        """Тест валидации глубокой вложенности"""
        config = ValidationConfig(max_dict_depth=2)
        validator = SecurityValidator(config)

        # Неглубокая вложенность должна пройти
        shallow_data = {"level1": {"level2": "value"}}
        result = validator.validate_dict(shallow_data)
        assert result == shallow_data

        # Глубокая вложенность должна вызвать исключение
        deep_data = {"level1": {"level2": {"level3": {"level4": "value"}}}}
        with pytest.raises(HTTPException):
            validator.validate_dict(deep_data)


if __name__ == "__main__":
    pytest.main([__file__])
