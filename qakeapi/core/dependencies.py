from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Type, TypeVar, get_type_hints
import inspect
from contextlib import AsyncExitStack
import asyncio
from inspect import signature, Parameter

T = TypeVar("T")

class Dependency(ABC):
    """Базовый класс для всех зависимостей"""
    
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
    async def register(self, dependency_type: Type[T], implementation: Dependency) -> None:
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
        self.dependencies: Dict[Type, Dict[str, Any]] = {}
        self.instances: Dict[str, Dict[Type, Any]] = {
            "singleton": {},
            "request": {},
            "transient": {}
        }
        self.scopes = ["singleton", "request", "transient"]
        
    async def register(
        self,
        dependency_type: Type[T],
        implementation: Dependency,
        scope: str = "singleton"
    ) -> None:
        """Регистрация зависимости"""
        if scope not in self.scopes:
            raise ValueError(f"Неизвестная область видимости: {scope}")
            
        if dependency_type not in self.dependencies:
            self.dependencies[dependency_type] = {}
            
        self.dependencies[dependency_type]["implementation"] = implementation
        self.dependencies[dependency_type]["scope"] = scope
        
    async def resolve(self, dependency_type: Type[T], scope: str = None) -> T:
        """Разрешение зависимости"""
        # Получаем информацию о зависимости
        dependency_info = self.dependencies.get(dependency_type)
        if not dependency_info:
            raise ValueError(f"Зависимость не зарегистрирована: {dependency_type}")
            
        # Используем scope из регистрации, если не указан явно
        scope = scope or dependency_info["scope"]
        
        if scope not in self.scopes:
            raise ValueError(f"Неизвестная область видимости: {scope}")
            
        dependency = dependency_info["implementation"]
        
        # Для transient scope всегда создаем новый экземпляр
        if scope == "transient":
            instance = await dependency.resolve()
            # Сохраняем экземпляр для очистки
            self.instances[scope][id(instance)] = instance
            return instance
            
        current_scope = self.instances[scope]
        
        # Проверяем наличие экземпляра в текущей области видимости
        if dependency_type not in current_scope:
            instance = await dependency.resolve()
            current_scope[dependency_type] = instance
            
        return current_scope[dependency_type]
        
    async def cleanup(self, scope: str) -> None:
        """Очистка зависимостей в указанной области видимости"""
        if scope not in self.scopes:
            raise ValueError(f"Неизвестная область видимости: {scope}")
            
        current_scope = self.instances[scope]
        
        # Очищаем все экземпляры в области видимости
        for key, instance in list(current_scope.items()):
            if hasattr(instance, "cleanup"):
                await instance.cleanup()
            del current_scope[key]
            
        # Очищаем все зависимости, даже если они не были разрешены
        for dependency_info in self.dependencies.values():
            if dependency_info["scope"] == scope:
                await dependency_info["implementation"].cleanup()
            
        # Создаем новый словарь для области видимости
        self.instances[scope] = {}
        
    async def cleanup_all(self) -> None:
        """Очистка всех зависимостей"""
        for scope in self.scopes:
            await self.cleanup(scope)

class Inject:
    """Декоратор для внедрения зависимостей"""
    
    def __init__(self, container: DependencyContainer):
        self.container = container
        
    def __call__(self, handler: Callable) -> Callable:
        sig = signature(handler)
        
        async def wrapper(*args, **kwargs):
            # Очищаем request scope перед каждым вызовом
            await self.container.cleanup("request")
            
            try:
                # Получаем все параметры функции
                for name, param in sig.parameters.items():
                    if name not in kwargs and param.annotation != Parameter.empty:
                        # Определяем scope на основе типа зависимости
                        scope = "request" if name == "request" else None
                        try:
                            kwargs[name] = await self.container.resolve(param.annotation, scope=scope)
                        except ValueError:
                            if name == "request" and args:
                                kwargs[name] = args[0]
                return await handler(**kwargs)
            finally:
                # Очищаем request scope после выполнения
                await self.container.cleanup("request")
            
        return wrapper

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