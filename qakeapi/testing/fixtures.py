"""
Test fixtures and factories system for QakeAPI.
"""
import random
import string
import uuid
from typing import Any, Dict, List, Optional, Type, TypeVar, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from functools import wraps

T = TypeVar('T')


@dataclass
class FixtureConfig:
    """Configuration for fixture generation."""
    seed: Optional[int] = None
    locale: str = "en_US"
    unique: bool = True
    min_count: int = 1
    max_count: int = 10


class FixtureFactory:
    """Factory for creating test fixtures."""
    
    def __init__(self, config: Optional[FixtureConfig] = None):
        self.config = config or FixtureConfig()
        if self.config.seed:
            random.seed(self.config.seed)
    
    def text(self, min_length: int = 10, max_length: int = 50) -> str:
        """Generate random text."""
        length = random.randint(min_length, max_length)
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def email(self) -> str:
        """Generate random email."""
        username = self.text(5, 15)
        domain = self.text(5, 10)
        return f"{username}@{domain}.com"
    
    def phone(self) -> str:
        """Generate random phone number."""
        return f"+1{random.randint(1000000000, 9999999999)}"
    
    def name(self) -> str:
        """Generate random name."""
        first_names = ["John", "Jane", "Bob", "Alice", "Charlie", "Diana", "Eve", "Frank"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def date(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> datetime:
        """Generate random date."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()
        
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randrange(days_between)
        return start_date + timedelta(days=random_days)
    
    def uuid(self) -> str:
        """Generate UUID."""
        return str(uuid.uuid4())
    
    def integer(self, min_value: int = 1, max_value: int = 1000) -> int:
        """Generate random integer."""
        return random.randint(min_value, max_value)
    
    def float(self, min_value: float = 0.0, max_value: float = 1000.0) -> float:
        """Generate random float."""
        return random.uniform(min_value, max_value)
    
    def boolean(self) -> bool:
        """Generate random boolean."""
        return random.choice([True, False])
    
    def choice(self, choices: List[Any]) -> Any:
        """Choose random item from list."""
        return random.choice(choices)
    
    def list(self, item_factory: Callable, min_count: int = 1, max_count: int = 5) -> List[Any]:
        """Generate list of items."""
        count = random.randint(min_count, max_count)
        return [item_factory() for _ in range(count)]
    
    def dict(self, key_factory: Callable, value_factory: Callable, 
             min_count: int = 1, max_count: int = 5) -> Dict[str, Any]:
        """Generate dictionary."""
        count = random.randint(min_count, max_count)
        return {key_factory(): value_factory() for _ in range(count)}


class TestFixtures:
    """Test fixtures manager."""
    
    def __init__(self, factory: Optional[FixtureFactory] = None):
        self.factory = factory or FixtureFactory()
        self._fixtures: Dict[str, Any] = {}
        self._fixture_factories: Dict[str, Callable] = {}
    
    def register_fixture(self, name: str, factory_func: Callable) -> None:
        """Register a fixture factory function."""
        self._fixture_factories[name] = factory_func
    
    def get_fixture(self, name: str, **kwargs) -> Any:
        """Get fixture by name."""
        if name in self._fixtures:
            return self._fixtures[name]
        
        if name in self._fixture_factories:
            fixture = self._fixture_factories[name](**kwargs)
            if self.factory.config.unique:
                self._fixtures[name] = fixture
            return fixture
        
        raise ValueError(f"Fixture '{name}' not found")
    
    def create_fixture(self, name: str, **kwargs) -> Any:
        """Create new fixture instance."""
        if name not in self._fixture_factories:
            raise ValueError(f"Fixture factory '{name}' not found")
        
        return self._fixture_factories[name](**kwargs)
    
    def clear_fixtures(self) -> None:
        """Clear all cached fixtures."""
        self._fixtures.clear()
    
    def list_fixtures(self) -> List[str]:
        """List all available fixtures."""
        return list(self._fixture_factories.keys())


# Predefined fixture factories
def user_fixture(factory: FixtureFactory) -> Dict[str, Any]:
    """Create user fixture."""
    return {
        "id": factory.uuid(),
        "username": factory.text(5, 15),
        "email": factory.email(),
        "name": factory.name(),
        "created_at": factory.date(),
        "is_active": factory.boolean(),
        "roles": factory.list(lambda: factory.choice(["user", "admin", "moderator"]), 1, 3)
    }


def post_fixture(factory: FixtureFactory) -> Dict[str, Any]:
    """Create post fixture."""
    return {
        "id": factory.uuid(),
        "title": factory.text(10, 50),
        "content": factory.text(50, 200),
        "author_id": factory.uuid(),
        "created_at": factory.date(),
        "updated_at": factory.date(),
        "tags": factory.list(lambda: factory.text(3, 10), 0, 5),
        "is_published": factory.boolean()
    }


def comment_fixture(factory: FixtureFactory) -> Dict[str, Any]:
    """Create comment fixture."""
    return {
        "id": factory.uuid(),
        "content": factory.text(20, 100),
        "author_id": factory.uuid(),
        "post_id": factory.uuid(),
        "created_at": factory.date(),
        "parent_id": factory.uuid() if factory.boolean() else None
    }


def product_fixture(factory: FixtureFactory) -> Dict[str, Any]:
    """Create product fixture."""
    return {
        "id": factory.uuid(),
        "name": factory.text(10, 30),
        "description": factory.text(50, 150),
        "price": factory.float(1.0, 1000.0),
        "category": factory.choice(["electronics", "clothing", "books", "home"]),
        "in_stock": factory.integer(0, 100),
        "created_at": factory.date(),
        "tags": factory.list(lambda: factory.text(3, 8), 0, 3)
    }


# Decorator for automatic fixture injection
def with_fixtures(*fixture_names: str):
    """Decorator to inject fixtures into test functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create fixtures instance
            fixtures = TestFixtures()
            
            # Register common fixtures
            factory = fixtures.factory
            fixtures.register_fixture("user", lambda: user_fixture(factory))
            fixtures.register_fixture("post", lambda: post_fixture(factory))
            fixtures.register_fixture("comment", lambda: comment_fixture(factory))
            fixtures.register_fixture("product", lambda: product_fixture(factory))
            
            # Get requested fixtures
            fixture_data = {}
            for name in fixture_names:
                fixture_data[name] = fixtures.get_fixture(name)
            
            # Add fixtures to kwargs
            kwargs.update(fixture_data)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator 