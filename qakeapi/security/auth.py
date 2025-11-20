"""
Enhanced authentication system with secure JWT and password hashing
"""
import os
import warnings
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass

# Conditional imports for Windows compatibility
try:
    from jose import JWTError, jwt
    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False
    # Stubs
    class JWTError(Exception): pass
    class jwt:
        @staticmethod
        def encode(*args, **kwargs): return "mock_token"
        @staticmethod
        def decode(*args, **kwargs): return {"sub": "mock_user"}

try:
    from passlib.context import CryptContext
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False
    # Stub
    class CryptContext:
        def __init__(self, *args, **kwargs): pass
        def hash(self, password): return hashlib.sha256(password.encode()).hexdigest()
        def verify(self, password, hash_val): return self.hash(password) == hash_val
from pydantic import BaseModel, Field

from ..core.exceptions import HTTPException
from ..utils.status import status


@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digits: bool = True
    password_require_special: bool = True


class TokenData(BaseModel):
    """Token data"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    scopes: list[str] = Field(default_factory=list)


class Token(BaseModel):
    """Token model"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class PasswordManager:
    """Manager for working with passwords"""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        
        # Use bcrypt if available, else simple hash for testing
        if PASSLIB_AVAILABLE:
            try:
                self.pwd_context = CryptContext(
                    schemes=["bcrypt"],
                    deprecated="auto",
                    bcrypt__rounds=12
                )
                # Test that bcrypt works
                self.pwd_context.hash("test")
                self._use_simple_hash = False
            except Exception:
                # If bcrypt doesn't work, use simple hash (for testing only!)
                warnings.warn("Bcrypt unavailable, using simple hash (unsafe for production!)")
                self.pwd_context = None
                self._use_simple_hash = True
        else:
            warnings.warn("Passlib unavailable, using simple hash (unsafe for production!)")
            self.pwd_context = None
            self._use_simple_hash = True
    
    def hash_password(self, password: str) -> str:
        """Hash password"""
        self.validate_password_strength(password)
        
        if self._use_simple_hash:
            # Simple hash with salt (for testing only!)
            salt = os.urandom(16).hex()
            hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return f"simple_hash${salt}${hash_obj.hex()}"
        else:
            return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        if self._use_simple_hash and hashed_password.startswith("simple_hash$"):
            # Parse simple hash
            parts = hashed_password.split('$')
            if len(parts) != 3:
                return False
            _, salt, stored_hash = parts
            hash_obj = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt.encode(), 100000)
            return hash_obj.hex() == stored_hash
        else:
            return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_password_strength(self, password: str) -> None:
        """Check password strength"""
        if len(password) < self.config.password_min_length:
            raise HTTPException(
                status.BAD_REQUEST,
                f"Password must contain at least {self.config.password_min_length} characters"
            )
        
        if self.config.password_require_uppercase and not any(c.isupper() for c in password):
            raise HTTPException(
                status.BAD_REQUEST,
                "Password must contain at least one uppercase letter"
            )
        
        if self.config.password_require_lowercase and not any(c.islower() for c in password):
            raise HTTPException(
                status.BAD_REQUEST,
                "Password must contain at least one lowercase letter"
            )
        
        if self.config.password_require_digits and not any(c.isdigit() for c in password):
            raise HTTPException(
                status.BAD_REQUEST,
                "Password must contain at least one digit"
            )
        
        if self.config.password_require_special and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            raise HTTPException(
                status.BAD_REQUEST,
                "Password must contain at least one special character"
            )


class JWTManager:
    """Manager for working with JWT tokens"""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        
        if self.config.secret_key == "your-secret-key-change-in-production":
            import warnings
            warnings.warn(
                "Using default secret key! Change SECRET_KEY in production!",
                UserWarning
            )
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.config.access_token_expire_minutes
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        if JOSE_AVAILABLE:
            return jwt.encode(
                to_encode,
                self.config.secret_key,
                algorithm=self.config.algorithm
            )
        else:
            # Stub for testing
            return f"mock_access_token_{data.get('sub', 'unknown')}"
    
    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create refresh token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=self.config.refresh_token_expire_days
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        if JOSE_AVAILABLE:
            return jwt.encode(
                to_encode,
                self.config.secret_key,
                algorithm=self.config.algorithm
            )
        else:
            # Stub for testing
            return f"mock_refresh_token_{data.get('sub', 'unknown')}"
    
    def create_token_pair(self, data: Dict[str, Any]) -> Token:
        """Создать пару токеноin (access + refresh)"""
        access_token = self.create_access_token(data)
        refresh_token = self.create_refresh_token(data)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.config.access_token_expire_minutes * 60
        )
    
    def verify_token(self, token: str, token_type: str = "access") -> TokenData:
        """Проinерandть and деcodeandроinать токен"""
        try:
            if JOSE_AVAILABLE:
                payload = jwt.decode(
                    token,
                    self.config.secret_key,
                    algorithms=[self.config.algorithm]
                )
            else:
                # Stub for testing
                if token.startswith("mock_"):
                    payload = {"sub": "mock_user", "type": token_type, "exp": 9999999999}
                else:
                    raise JWTError("Invalid token")
            
            # Проinеряем type токена
            if payload.get("type") != token_type:
                raise HTTPException(
                    status.UNAUTHORIZED,
                    f"Неinерный type токена. Ожandдался: {token_type}"
                )
            
            # Проinеряем срок дейстinandя
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status.UNAUTHORIZED,
                    "Токен andстек"
                )
            
            return TokenData(
                user_id=payload.get("user_id"),
                username=payload.get("username"),
                email=payload.get("email"),
                scopes=payload.get("scopes", [])
            )
            
        except JWTError as e:
            raise HTTPException(
                status.UNAUTHORIZED,
                f"Не удалось inалandдandроinать токен: {str(e)}"
            )
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Обноinandть access токен andспользуя refresh токен"""
        token_data = self.verify_token(refresh_token, "refresh")
        
        # Создаем ноinый access токен с темand же даннымand
        new_data = {
            "user_id": token_data.user_id,
            "username": token_data.username,
            "email": token_data.email,
            "scopes": token_data.scopes
        }
        
        return self.create_access_token(new_data)
    
    def decode_token_without_verification(self, token: str) -> Dict[str, Any]:
        """Деcodeandроinать токен без проinеркand (for отладкand)"""
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )
        except JWTError:
            return {}


# Глобальные экземпляры for удобстinа
default_config = SecurityConfig()
password_manager = PasswordManager(default_config)
jwt_manager = JWTManager(default_config)


