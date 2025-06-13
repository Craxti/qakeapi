from typing import Any, Dict

import pytest

from qakeapi.core.dependencies import Dependency, DependencyContainer, inject


class ConfigDependency(Dependency):
    async def resolve(self) -> Dict[str, Any]:
        return {"app_name": "Test App", "version": "1.0.0"}


class DatabaseDependency(Dependency):
    def __init__(self):
        super().__init__(scope="singleton")
        self.connection = None
        self.instance_id = id(self)

    async def resolve(self) -> Any:
        if not self.connection:
            self.connection = {"connected": True, "instance_id": self.instance_id}
        return self.connection

    async def cleanup(self) -> None:
        if self.connection:
            self.connection = None


class ServiceDependency(Dependency):
    async def resolve(self) -> Dict[str, Any]:
        return {"service": "test"}


@pytest.fixture
def container():
    return DependencyContainer()


@pytest.mark.asyncio
async def test_dependency_resolution():
    container = DependencyContainer()
    config = ConfigDependency()
    container.register(config)

    result = await container.resolve(ConfigDependency)
    assert result == {"app_name": "Test App", "version": "1.0.0"}


@pytest.mark.asyncio
async def test_singleton_scope():
    container = DependencyContainer()
    db = DatabaseDependency()
    container.register(db)

    # First resolution
    conn1 = await container.resolve(DatabaseDependency)
    assert conn1["connected"] is True

    # Second resolution should return the same instance
    conn2 = await container.resolve(DatabaseDependency)
    assert conn1 is conn2


@pytest.mark.asyncio
async def test_cleanup():
    container = DependencyContainer()
    db = DatabaseDependency()
    container.register(db)

    conn = await container.resolve(DatabaseDependency)
    assert conn["connected"] is True

    await container.cleanup()
    assert db.connection is None


@pytest.mark.asyncio
async def test_inject_decorator():
    container = DependencyContainer()
    config = ConfigDependency()
    db = DatabaseDependency()
    container.register(config)
    container.register(db)

    @inject(ConfigDependency, DatabaseDependency)
    async def handler(request, config, db):
        return {"config": config, "db": db}

    result = await handler({"type": "http"}, container=container)
    assert result["config"] == {"app_name": "Test App", "version": "1.0.0"}
    assert result["db"]["connected"] is True


@pytest.mark.asyncio
async def test_multiple_dependencies():
    container = DependencyContainer()
    db = DatabaseDependency()
    service = ServiceDependency()
    container.register(db)
    container.register(service)

    @inject(DatabaseDependency, ServiceDependency)
    async def handler(request, db, service):
        return {"db": db, "service": service}

    result = await handler({"type": "http"}, container=container)
    assert result["db"]["connected"] is True
    assert result["service"] == {"service": "test"}
