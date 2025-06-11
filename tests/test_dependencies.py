import pytest
from typing import List, Optional, Dict, Any
from qakeapi.core.dependencies import (
    Dependency,
    DependencyContainer,
    Inject,
    Database,
    DatabaseDependency
)

class MockDatabase(Database):
    def __init__(self):
        self.connected = False
        self.queries: List[str] = []
        self.instance_id: int = 0  # Уникальный идентификатор экземпляра
        
    async def connect(self) -> None:
        self.connected = True
        
    async def disconnect(self) -> None:
        self.connected = False
        
    async def query(self, sql: str) -> list:
        self.queries.append(sql)
        return []
        
    def __eq__(self, other):
        if not isinstance(other, MockDatabase):
            return False
        return self.instance_id == other.instance_id
        
    def __hash__(self):
        return hash(self.instance_id)

class MockDatabaseDependency(Dependency):
    def __init__(self):
        self.instances: List[MockDatabase] = []
        self.instance_counter = 0
        
    async def resolve(self) -> Database:
        self.instance_counter += 1
        db = MockDatabase()
        db.instance_id = self.instance_counter
        self.instances.append(db)
        return db
        
    async def cleanup(self) -> None:
        for db in self.instances:
            await db.disconnect()

class TestDependency(Dependency):
    def __init__(self, value: str = "test"):
        self.value = value
        
    async def resolve(self) -> str:
        return self.value

class TestService:
    def __init__(self, value: str):
        self.value = value

@pytest.fixture
def container():
    return DependencyContainer()

@pytest.mark.asyncio
async def test_dependency_resolution(container):
    """Тест разрешения зависимости"""
    # Регистрируем зависимость
    dep = TestDependency()
    await container.register(str, dep)
    
    # Проверяем разрешение
    value = await container.resolve(str)
    assert value == "test"

@pytest.mark.asyncio
async def test_singleton_scope(container):
    """Тест синглтон скопа"""
    # Регистрируем зависимость как синглтон
    dep = TestDependency()
    await container.register(str, dep, scope="singleton")
    
    # Проверяем, что получаем один и тот же экземпляр
    value1 = await container.resolve(str)
    value2 = await container.resolve(str)
    assert value1 == value2

@pytest.mark.asyncio
async def test_transient_scope(container):
    """Тест транзиентного скопа"""
    # Регистрируем зависимость как транзиентную
    class CounterDependency(Dependency):
        def __init__(self):
            self.counter = 0
            
        async def resolve(self) -> int:
            self.counter += 1
            return self.counter
    
    dep = CounterDependency()
    await container.register(int, dep, scope="transient")
    
    # Проверяем, что получаем разные значения
    value1 = await container.resolve(int)
    value2 = await container.resolve(int)
    assert value1 != value2

@pytest.mark.asyncio
async def test_inject_decorator(container):
    """Тест декоратора Inject"""
    # Регистрируем зависимость
    dep = TestDependency("injected")
    await container.register(str, dep)
    
    # Создаем тестовый обработчик с внедрением зависимости
    @Inject(container)
    async def test_handler(request: Dict[str, Any], value: str):
        return {
            "status": 200,
            "headers": [(b"content-type", b"application/json")],
            "body": value.encode()
        }
    
    # Проверяем внедрение зависимости
    response = await test_handler({"method": "GET", "path": "/"})
    assert response["body"] == b"injected"

@pytest.mark.asyncio
async def test_cleanup(container):
    """Тест очистки зависимостей"""
    cleanup_called = False
    
    class CleanupDependency(Dependency):
        async def resolve(self) -> str:
            return "test"
            
        async def cleanup(self):
            nonlocal cleanup_called
            cleanup_called = True
    
    # Регистрируем зависимость
    dep = CleanupDependency()
    await container.register(str, dep)
    
    # Очищаем контейнер
    await container.cleanup_all()
    assert cleanup_called

@pytest.mark.asyncio
class TestDependencyContainer:
    async def test_register_and_resolve(self):
        container = DependencyContainer()
        dependency = MockDatabaseDependency()
        await container.register(Database, dependency)
        
        # Получаем зависимость
        db = await container.resolve(Database)
        assert isinstance(db, MockDatabase)
        assert len(dependency.instances) == 1
        
    async def test_singleton_scope(self):
        container = DependencyContainer()
        dependency = MockDatabaseDependency()
        await container.register(Database, dependency)
        
        # Получаем два экземпляра
        db1 = await container.resolve(Database)
        db2 = await container.resolve(Database)
        
        # Проверяем, что это один и тот же экземпляр
        assert len(dependency.instances) == 1
        assert db1 is db2
        
    async def test_request_scope(self):
        container = DependencyContainer()
        dependency = MockDatabaseDependency()
        await container.register(Database, dependency, scope="request")
        
        # Получаем экземпляр
        db1 = await container.resolve(Database, scope="request")
        
        # Очищаем scope
        await container.cleanup("request")
        
        # Получаем новый экземпляр
        db2 = await container.resolve(Database, scope="request")
        
        # Проверяем, что это разные экземпляры
        assert len(dependency.instances) == 2
        assert db1 is not db2
        
    async def test_cleanup(self):
        container = DependencyContainer()
        dependency = MockDatabaseDependency()
        await container.register(Database, dependency)
        
        # Получаем зависимость
        db = await container.resolve(Database)
        assert isinstance(db, MockDatabase)
        
        # Очищаем scope
        await container.cleanup("singleton")
        
        # Получаем новую зависимость
        new_db = await container.resolve(Database)
        assert isinstance(new_db, MockDatabase)
        assert len(dependency.instances) == 2
        assert db is not new_db
        
    async def test_invalid_scope(self):
        container = DependencyContainer()
        dependency = MockDatabaseDependency()
        
        with pytest.raises(ValueError):
            await container.register(Database, dependency, scope="invalid")
            
        with pytest.raises(ValueError):
            await container.resolve(Database, scope="invalid")
            
    async def test_unregistered_dependency(self):
        container = DependencyContainer()
        
        with pytest.raises(ValueError):
            await container.resolve(Database)

@pytest.mark.asyncio
class TestInject:
    async def test_dependency_injection(self):
        container = DependencyContainer()
        dependency = MockDatabaseDependency()
        await container.register(Database, dependency)
        
        @Inject(container)
        async def handler(db: Database):
            await db.query("SELECT 1")
            return db
            
        # Вызываем обработчик
        db = await handler()
        assert isinstance(db, MockDatabase)
        assert db.queries == ["SELECT 1"]
        assert len(dependency.instances) == 1
        
    async def test_multiple_dependencies(self):
        container = DependencyContainer()
        dependency = MockDatabaseDependency()
        await container.register(Database, dependency)
        
        class Service:
            pass
            
        class ServiceDependency(Dependency):
            async def resolve(self) -> Service:
                return Service()
                
        await container.register(Service, ServiceDependency())
        
        @Inject(container)
        async def handler(db: Database, service: Service):
            assert isinstance(db, MockDatabase)
            assert isinstance(service, Service)
            return True
            
        assert await handler()
        assert len(dependency.instances) == 1
        
    async def test_cleanup_after_handler(self):
        container = DependencyContainer()
        dependency = MockDatabaseDependency()
        await container.register(Database, dependency, scope="request")
        
        @Inject(container)
        async def handler(db: Database):
            print(f"Handler called with db instance: {id(db)}, instance_id: {db.instance_id}")
            return db
            
        # Вызываем обработчик дважды
        print("\nBefore first handler call")
        db1 = await handler()
        db1_id = db1.instance_id
        print(f"After first handler call, instances: {[db.instance_id for db in dependency.instances]}")
        
        print("\nBefore second handler call")
        db2 = await handler()
        db2_id = db2.instance_id
        print(f"After second handler call, instances: {[db.instance_id for db in dependency.instances]}")
        
        # Проверяем, что это разные экземпляры
        assert db1_id != db2_id, "db1 and db2 should have different instance_ids" 