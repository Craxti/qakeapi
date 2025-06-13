import pytest
from datetime import timedelta
from qakeapi.security.jwt_auth import JWTConfig, JWTAuthBackend, AuthenticationError

@pytest.fixture
def jwt_config():
    return JWTConfig(
        secret_key="test_secret_key",
        algorithm="HS256",
        access_token_expire_minutes=30
    )

@pytest.fixture
def auth_backend(jwt_config):
    backend = JWTAuthBackend(jwt_config)
    backend.add_user("test_user", "test_pass", ["user"])
    backend.add_user("admin", "admin_pass", ["admin", "user"])
    return backend

@pytest.mark.asyncio
async def test_jwt_auth_success(auth_backend):
    # Test username/password authentication
    credentials = {"username": "test_user", "password": "test_pass"}
    user = await auth_backend.authenticate(credentials)
    assert user is not None
    assert user.username == "test_user"
    assert user.roles == ["user"]
    
    # Create and verify JWT token
    token = auth_backend.create_access_token({"sub": user.username})
    token_user = await auth_backend.authenticate({"token": token})
    assert token_user is not None
    assert token_user.username == user.username
    assert token_user.roles == user.roles

@pytest.mark.asyncio
async def test_jwt_auth_wrong_password(auth_backend):
    credentials = {"username": "test_user", "password": "wrong_pass"}
    user = await auth_backend.authenticate(credentials)
    assert user is None

@pytest.mark.asyncio
async def test_jwt_auth_invalid_token(auth_backend):
    with pytest.raises(AuthenticationError):
        await auth_backend.authenticate({"token": "invalid_token"})

@pytest.mark.asyncio
async def test_jwt_auth_expired_token(auth_backend):
    # Create token that expires immediately
    token = auth_backend.create_access_token(
        {"sub": "test_user"},
        expires_delta=timedelta(microseconds=1)
    )
    # Wait for token to expire
    import time
    time.sleep(0.1)
    
    with pytest.raises(AuthenticationError):
        await auth_backend.authenticate({"token": token})

@pytest.mark.asyncio
async def test_get_user(auth_backend):
    user = await auth_backend.get_user("admin")
    assert user is not None
    assert user.username == "admin"
    assert set(user.roles) == {"admin", "user"}
    
    user = await auth_backend.get_user("nonexistent")
    assert user is None 