"""
Тесты для системы валидации данных
"""
import pytest
from qakeapi.utils.validation import (
    StringValidator,
    IntegerValidator,
    FloatValidator,
    BooleanValidator,
    EmailValidator,
    URLValidator,
    ListValidator,
    DictValidator,
    DataValidator,
    ValidationResult,
)


class TestStringValidator:
    """Тесты валидатора строк"""

    def test_valid_string(self):
        validator = StringValidator()
        result = validator.validate("test string", "field")
        assert result.is_valid
        assert result.data == "test string"

    def test_min_length(self):
        validator = StringValidator(min_length=5)

        # Слишком короткая строка
        result = validator.validate("abc", "field")
        assert not result.is_valid
        assert "at least 5 characters" in result.errors[0]

        # Подходящая длина
        result = validator.validate("abcde", "field")
        assert result.is_valid

    def test_max_length(self):
        validator = StringValidator(max_length=5)

        # Слишком длинная строка
        result = validator.validate("abcdef", "field")
        assert not result.is_valid
        assert "at most 5 characters" in result.errors[0]

        # Подходящая длина
        result = validator.validate("abcde", "field")
        assert result.is_valid

    def test_pattern(self):
        validator = StringValidator(pattern=r"^\d+$")  # только цифры

        # Неподходящий паттерн
        result = validator.validate("abc123", "field")
        assert not result.is_valid

        # Подходящий паттерн
        result = validator.validate("123", "field")
        assert result.is_valid

    def test_non_string(self):
        validator = StringValidator()
        result = validator.validate(123, "field")
        assert not result.is_valid
        assert "must be a string" in result.errors[0]


class TestIntegerValidator:
    """Тесты валидатора целых чисел"""

    def test_valid_integer(self):
        validator = IntegerValidator()
        result = validator.validate(42, "field")
        assert result.is_valid
        assert result.data == 42

    def test_string_conversion(self):
        validator = IntegerValidator()
        result = validator.validate("42", "field")
        assert result.is_valid
        assert result.data == 42

    def test_invalid_string(self):
        validator = IntegerValidator()
        result = validator.validate("abc", "field")
        assert not result.is_valid
        assert "valid integer" in result.errors[0]

    def test_min_value(self):
        validator = IntegerValidator(min_value=10)

        result = validator.validate(5, "field")
        assert not result.is_valid
        assert "at least 10" in result.errors[0]

        result = validator.validate(15, "field")
        assert result.is_valid

    def test_max_value(self):
        validator = IntegerValidator(max_value=100)

        result = validator.validate(150, "field")
        assert not result.is_valid
        assert "at most 100" in result.errors[0]

        result = validator.validate(50, "field")
        assert result.is_valid

    def test_boolean_rejection(self):
        validator = IntegerValidator()
        result = validator.validate(True, "field")
        assert not result.is_valid


class TestFloatValidator:
    """Тесты валидатора чисел с плавающей точкой"""

    def test_valid_float(self):
        validator = FloatValidator()
        result = validator.validate(3.14, "field")
        assert result.is_valid
        assert result.data == 3.14

    def test_integer_to_float(self):
        validator = FloatValidator()
        result = validator.validate(42, "field")
        assert result.is_valid
        assert result.data == 42.0

    def test_string_conversion(self):
        validator = FloatValidator()
        result = validator.validate("3.14", "field")
        assert result.is_valid
        assert result.data == 3.14

    def test_range_validation(self):
        validator = FloatValidator(min_value=0.0, max_value=10.0)

        result = validator.validate(-1.0, "field")
        assert not result.is_valid

        result = validator.validate(15.0, "field")
        assert not result.is_valid

        result = validator.validate(5.0, "field")
        assert result.is_valid


class TestBooleanValidator:
    """Тесты валидатора булевых значений"""

    def test_valid_boolean(self):
        validator = BooleanValidator()

        result = validator.validate(True, "field")
        assert result.is_valid
        assert result.data is True

        result = validator.validate(False, "field")
        assert result.is_valid
        assert result.data is False

    def test_string_conversion(self):
        validator = BooleanValidator()

        # True values
        for value in ["true", "True", "1", "yes", "on"]:
            result = validator.validate(value, "field")
            assert result.is_valid
            assert result.data is True

        # False values
        for value in ["false", "False", "0", "no", "off"]:
            result = validator.validate(value, "field")
            assert result.is_valid
            assert result.data is False

    def test_number_conversion(self):
        validator = BooleanValidator()

        result = validator.validate(1, "field")
        assert result.is_valid
        assert result.data is True

        result = validator.validate(0, "field")
        assert result.is_valid
        assert result.data is False


class TestEmailValidator:
    """Тесты валидатора email"""

    def test_valid_emails(self):
        validator = EmailValidator()

        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@example.com",
        ]

        for email in valid_emails:
            result = validator.validate(email, "field")
            assert result.is_valid, f"Email {email} should be valid"

    def test_invalid_emails(self):
        validator = EmailValidator()

        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com",
            "test@.com",
        ]

        for email in invalid_emails:
            result = validator.validate(email, "field")
            assert not result.is_valid, f"Email {email} should be invalid"


class TestListValidator:
    """Тесты валидатора списков"""

    def test_valid_list(self):
        validator = ListValidator()
        result = validator.validate([1, 2, 3], "field")
        assert result.is_valid
        assert result.data == [1, 2, 3]

    def test_item_validation(self):
        item_validator = StringValidator(min_length=2)
        validator = ListValidator(item_validator=item_validator)

        # Все элементы валидны
        result = validator.validate(["ab", "cd", "ef"], "field")
        assert result.is_valid

        # Один элемент невалиден
        result = validator.validate(["ab", "c", "ef"], "field")
        assert not result.is_valid

    def test_min_max_items(self):
        validator = ListValidator(min_items=2, max_items=4)

        # Слишком мало элементов
        result = validator.validate([1], "field")
        assert not result.is_valid

        # Слишком много элементов
        result = validator.validate([1, 2, 3, 4, 5], "field")
        assert not result.is_valid

        # Подходящее количество
        result = validator.validate([1, 2, 3], "field")
        assert result.is_valid


class TestDictValidator:
    """Тесты валидатора словарей"""

    def test_schema_validation(self):
        schema = {
            "name": StringValidator(min_length=2),
            "age": IntegerValidator(min_value=0),
        }
        validator = DictValidator(schema=schema)

        # Валидные данные
        data = {"name": "John", "age": 25}
        result = validator.validate(data, "field")
        assert result.is_valid

        # Невалидные данные
        data = {"name": "J", "age": -5}
        result = validator.validate(data, "field")
        assert not result.is_valid

    def test_extra_fields(self):
        schema = {"name": StringValidator()}

        # Разрешаем дополнительные поля
        validator = DictValidator(schema=schema, allow_extra=True)
        data = {"name": "John", "extra": "value"}
        result = validator.validate(data, "field")
        assert result.is_valid
        assert "extra" in result.data

        # Запрещаем дополнительные поля
        validator = DictValidator(schema=schema, allow_extra=False)
        result = validator.validate(data, "field")
        assert not result.is_valid


class TestDataValidator:
    """Тесты основного валидатора данных"""

    def test_complete_validation(self):
        schema = {
            "name": StringValidator(min_length=2, max_length=50),
            "email": EmailValidator(),
            "age": IntegerValidator(min_value=0, max_value=150, required=False),
            "active": BooleanValidator(required=False),
        }
        validator = DataValidator(schema)

        # Полные валидные данные
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "active": True,
        }
        result = validator.validate(data)
        assert result.is_valid

        # Минимальные валидные данные
        data = {"name": "Jane", "email": "jane@example.com"}
        result = validator.validate(data)
        assert result.is_valid

        # Невалидные данные
        data = {
            "name": "J",  # слишком короткое
            "email": "invalid-email",  # невалидный email
            "age": -5,  # отрицательный возраст
        }
        result = validator.validate(data)
        assert not result.is_valid
        assert len(result.errors) >= 3

    def test_json_validation(self):
        schema = {"name": StringValidator()}
        validator = DataValidator(schema)

        # Валидный JSON
        result = validator.validate_json('{"name": "John"}')
        assert result.is_valid

        # Невалидный JSON
        result = validator.validate_json('{"name": }')
        assert not result.is_valid
        assert "Invalid JSON" in result.errors[0]


class TestRequiredAndNone:
    """Тесты обязательных полей и None значений"""

    def test_required_field(self):
        validator = StringValidator(required=True)

        # None для обязательного поля
        result = validator.validate(None, "field")
        assert not result.is_valid
        assert "required" in result.errors[0]

    def test_optional_field(self):
        validator = StringValidator(required=False)

        # None для необязательного поля
        result = validator.validate(None, "field")
        assert result.is_valid
        assert result.data is None

    def test_allow_none(self):
        validator = StringValidator(required=True, allow_none=True)

        # None разрешен
        result = validator.validate(None, "field")
        assert result.is_valid
        assert result.data is None
