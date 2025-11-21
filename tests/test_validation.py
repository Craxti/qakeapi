"""
Tests for validation module.
"""

from datetime import datetime

import pytest

from qakeapi.validation import (
    BaseModel,
    BooleanValidator,
    DateTimeValidator,
    DictValidator,
    EmailValidator,
    Field,
    FloatValidator,
    IntegerValidator,
    ListValidator,
    StringValidator,
    URLValidator,
    ValidationError,
)


def test_string_validator():
    """Test StringValidator."""
    validator = StringValidator(min_length=3, max_length=10)

    assert validator.validate("test") == "test"
    assert validator.validate("  test  ") == "test"  # strip

    with pytest.raises(ValidationError):
        validator.validate("ab")  # too short

    with pytest.raises(ValidationError):
        validator.validate("this is too long")  # too long


def test_integer_validator():
    """Test IntegerValidator."""
    validator = IntegerValidator(min_value=0, max_value=100)

    assert validator.validate(50) == 50
    assert validator.validate("50") == 50

    with pytest.raises(ValidationError):
        validator.validate(-1)  # too small

    with pytest.raises(ValidationError):
        validator.validate(200)  # too large


def test_float_validator():
    """Test FloatValidator."""
    validator = FloatValidator(min_value=0.0, max_value=1.0)

    assert validator.validate(0.5) == 0.5
    assert validator.validate("0.5") == 0.5

    with pytest.raises(ValidationError):
        validator.validate(-0.1)  # too small


def test_boolean_validator():
    """Test BooleanValidator."""
    validator = BooleanValidator()

    assert validator.validate(True) is True
    assert validator.validate("true") is True
    assert validator.validate("1") is True
    assert validator.validate("false") is False
    assert validator.validate("0") is False


def test_email_validator():
    """Test EmailValidator."""
    validator = EmailValidator()

    assert validator.validate("test@example.com") == "test@example.com"
    assert (
        validator.validate("user.name+tag@example.co.uk")
        == "user.name+tag@example.co.uk"
    )

    with pytest.raises(ValidationError):
        validator.validate("invalid-email")

    with pytest.raises(ValidationError):
        validator.validate("test@")


def test_url_validator():
    """Test URLValidator."""
    validator = URLValidator()

    assert validator.validate("https://example.com") == "https://example.com"
    assert validator.validate("http://example.com/path") == "http://example.com/path"

    with pytest.raises(ValidationError):
        validator.validate("not-a-url")

    with pytest.raises(ValidationError):
        validator.validate("ftp://example.com")  # wrong scheme


def test_datetime_validator():
    """Test DateTimeValidator."""
    validator = DateTimeValidator()

    dt = validator.validate("2023-01-01T12:00:00")
    assert isinstance(dt, datetime)

    dt = validator.validate("2023-01-01")
    assert isinstance(dt, datetime)

    with pytest.raises(ValidationError):
        validator.validate("invalid-date")


def test_list_validator():
    """Test ListValidator."""
    validator = ListValidator(
        item_validator=IntegerValidator(),
        min_length=1,
        max_length=5,
    )

    result = validator.validate([1, 2, 3])
    assert result == [1, 2, 3]

    with pytest.raises(ValidationError):
        validator.validate([])  # too short

    with pytest.raises(ValidationError):
        validator.validate([1, 2, 3, 4, 5, 6])  # too long


def test_dict_validator():
    """Test DictValidator."""
    validator = DictValidator(
        schema={
            "name": StringValidator(),
            "age": IntegerValidator(),
        },
        required_keys=["name"],
    )

    result = validator.validate({"name": "John", "age": 30})
    assert result["name"] == "John"
    assert result["age"] == 30

    with pytest.raises(ValidationError):
        validator.validate({})  # missing required key


def test_base_model():
    """Test BaseModel."""

    class User(BaseModel):
        name: str
        age: int
        email: str

    user = User(name="John", age=30, email="john@example.com")
    assert user.name == "John"
    assert user.age == 30

    data = user.dict()
    assert data["name"] == "John"
    assert data["age"] == 30


def test_base_model_with_field():
    """Test BaseModel with Field definitions."""

    class User(BaseModel):
        name = Field(StringValidator(min_length=3))
        age = Field(IntegerValidator(min_value=0))
        email = Field(EmailValidator())

    user = User(name="John", age=30, email="john@example.com")
    assert user.name == "John"

    with pytest.raises(ValidationError):
        User(name="Jo", age=30, email="john@example.com")  # name too short
