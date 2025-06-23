"""
Модуль валидации данных для QakeAPI.
"""
from typing import Any, Optional, Type, TypeVar
from datetime import datetime
import re
from pydantic import BaseModel, Field, validator, EmailStr, constr

T = TypeVar('T', bound=BaseModel)

class ValidationError(Exception):
    """Custom validation error."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class CommonValidators:
    """Common validation utilities."""
    
    @staticmethod
    def validate_phone(v: str) -> str:
        """Validate phone number format."""
        pattern = r'^\+?1?\d{9,15}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid phone number format')
        return v

    @staticmethod
    def validate_password(v: str) -> str:
        """
        Validate password strength.
        Must contain at least:
        - 8 characters
        - 1 uppercase letter
        - 1 lowercase letter
        - 1 number
        - 1 special character
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain special character')
        return v

    @staticmethod
    def validate_future_date(v: datetime) -> datetime:
        """Validate that date is in the future."""
        if v <= datetime.now():
            raise ValueError('Date must be in the future')
        return v

# Common validation models
class UserBase(BaseModel):
    """Base user validation model."""
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = None

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v

    @validator('phone')
    def phone_format(cls, v):
        if v is not None:
            return CommonValidators.validate_phone(v)
        return v

class CreateUser(UserBase):
    """Модель для создания пользователя."""
    password: constr(min_length=8)

    @validator('password')
    def validate_password(cls, v):
        """Проверка сложности пароля."""
        if not any(c.isupper() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        if not any(c.islower() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну строчную букву')
        if not any(c.isdigit() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        return v

class UpdateUser(UserBase):
    """Модель для обновления пользователя."""
    password: Optional[constr(min_length=8)] = None
    email: Optional[EmailStr] = None

    @validator('password')
    def validate_password(cls, v):
        """Проверка сложности пароля."""
        if v is None:
            return v
        if not any(c.isupper() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        if not any(c.islower() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну строчную букву')
        if not any(c.isdigit() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        return v

class PaginationParams(BaseModel):
    """Параметры пагинации."""
    page: int = 1
    per_page: int = 10

    @validator('page')
    def validate_page(cls, v):
        """Проверка номера страницы."""
        if v < 1:
            raise ValueError('Номер страницы должен быть больше 0')
        return v

    @validator('per_page')
    def validate_per_page(cls, v):
        """Проверка количества элементов на странице."""
        if v < 1:
            raise ValueError('Количество элементов на странице должно быть больше 0')
        if v > 100:
            raise ValueError('Количество элементов на странице не может быть больше 100')
        return v

class DateRangeParams(BaseModel):
    """Date range parameters validation."""
    start_date: datetime
    end_date: datetime

    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

def validate_model(model: Type[T], data: Any) -> T:
    """
    Validate data against a Pydantic model.
    
    Args:
        model: Pydantic model class
        data: Data to validate
        
    Returns:
        Validated model instance
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        return model.parse_obj(data)
    except Exception as e:
        raise ValidationError("validation", str(e))

# Example usage:
"""
@app.post("/users/")
async def create_user(user_data: CreateUser):
    # Data is already validated
    return await db.create_user(user_data.dict())

@app.get("/items/")
async def list_items(pagination: PaginationParams):
    skip = (pagination.page - 1) * pagination.per_page
    return await db.get_items(
        skip=skip,
        limit=pagination.per_page
    )

@app.get("/sales/")
async def get_sales(date_range: DateRangeParams):
    return await db.get_sales(
        start_date=date_range.start_date,
        end_date=date_range.end_date
    )
""" 