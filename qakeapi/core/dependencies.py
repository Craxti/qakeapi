import asyncio
import inspect
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from functools import wraps
from inspect import Parameter, signature
from typing import Any, Callable, Dict, Optional, Type, TypeVar, get_type_hints

T = TypeVar("T")


class Dependency(ABC):
    """Базовый класс для всех зависимостей"""

    def __init__(self, scope: str = "request"):
        """Initialize dependency

        Args:
            scope: Dependency scope ("singleton", "request", "transient")
        """
        self.scope = scope

    @abstractmethod
    async def resolve(self) -> Any:
        """Разрешить зависимость"""
        pass

    async def cleanup(self) -> None:
        """Очистка ресурсов"""
        pass


class DependencyProvider(ABC):
    """Интерфейс для провайдера зависимостей"""

    @abstractmethod
    async def get(self, dependency_type: Type[T]) -> T:
        """Получить зависимость по типу"""
        pass

    @abstractmethod
    async def register(
        self, dependency_type: Type[T], implementation: Dependency
    ) -> None:
        """Зарегистрировать зависимость"""
        pass


class Scope:
    """Область видимости зависимостей"""

    def __init__(self):
        self.instances: Dict[Type, Any] = {}
        self.exit_stack = AsyncExitStack()

    async def cleanup(self):
        """Очистка ресурсов в области видимости"""
        # Очищаем ресурсы через exit_stack
        await self.exit_stack.aclose()

        # Очищаем все экземпляры
        for instance in self.instances.values():
            if hasattr(instance, "cleanup"):
                await instance.cleanup()

        # Очищаем словарь экземпляров
        self.instances.clear()

        # Создаем новый exit_stack
        self.exit_stack = AsyncExitStack()

    def add_instance(self, instance: Any, key: Any = None) -> None:
        """Добавить экземпляр в scope"""
        if key is None:
            key = type(instance)
        self.instances[key] = instance

    def get_instance(self, key: Any) -> Optional[Any]:
        """Получить экземпляр из scope"""
        return self.instances.get(key)


class DependencyContainer:
    """Контейнер зависимостей"""

    def __init__(self):
        self._dependencies: Dict[Type[Dependency], Dependency] = {}
        self._instances: Dict[Type[Dependency], Any] = {}

    def register(self, dependency: Dependency) -> None:
        """Register dependency"""
        self._dependencies[type(dependency)] = dependency

    async def resolve(self, dependency_type: Type[T]) -> T:
        """Resolve dependency instance"""
        if dependency_type not in self._dependencies:
            raise ValueError(f"Dependency {dependency_type} not registered")

        dependency = self._dependencies[dependency_type]

        if dependency.scope == "singleton":
            if dependency_type not in self._instances:
                self._instances[dependency_type] = await dependency.resolve()
            return self._instances[dependency_type]
        elif dependency.scope == "request":
            return await dependency.resolve()
        elif dependency.scope == "transient":
            return await dependency.resolve()
        else:
            raise ValueError(f"Invalid dependency scope: {dependency.scope}")

    async def cleanup(self) -> None:
        """Cleanup all dependencies"""
        for dependency in self._dependencies.values():
            await dependency.cleanup()
        self._instances.clear()

    async def cleanup_all(self) -> None:
        """Cleanup all dependencies (alias for cleanup)"""
        await self.cleanup()


def inject(*dependencies: Type[Dependency]):
    """Decorator for injecting dependencies into handler functions"""

    def decorator(handler: Callable) -> Callable:
        if not inspect.iscoroutinefunction(handler):
            raise TypeError("Handler must be a coroutine function")

        @wraps(handler)
        async def wrapper(
            request: Any, container: Optional[DependencyContainer] = None, **kwargs
        ) -> Any:
            # Попробовать взять контейнер из request, если не передан явно
            if not container:
                container = getattr(
                    request, "dependency_container", None
                ) or request.scope.get("dependency_container")
            if not container:
                raise ValueError("DependencyContainer not provided")

            # Resolve dependencies
            resolved_deps = []
            for dep_type in dependencies:
                resolved = await container.resolve(dep_type)
                resolved_deps.append(resolved)

            # Call handler with resolved dependencies
            return await handler(request, *resolved_deps, **kwargs)

        # Store dependencies for introspection
        setattr(wrapper, "__dependencies__", dependencies)
        return wrapper

    return decorator


# Примеры использования
class Database(ABC):
    """Интерфейс для работы с базой данных"""

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def query(self, sql: str) -> list:
        pass


class DatabaseDependency(Dependency):
    """Зависимость для работы с базой данных"""

    def __init__(self, connection_string: str):
        super().__init__()
        self.connection_string = connection_string

    async def resolve(self) -> Database:
        # Здесь должна быть реальная реализация базы данных
        return await self.create_database()

    async def create_database(self) -> Database:
        # Пример реализации
        class PostgresDatabase(Database):
            async def __aenter__(self):
                await self.connect()
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                await self.disconnect()

            async def connect(self) -> None:
                print(f"Подключение к базе данных: {self.connection_string}")

            async def disconnect(self) -> None:
                print("Отключение от базы данных")

            async def query(self, sql: str) -> list:
                print(f"Выполнение запроса: {sql}")
                return []

        db = PostgresDatabase()
        db.connection_string = self.connection_string
        return db
