"""
Database testing utilities with test isolation for QakeAPI.
"""
import asyncio
import tempfile
import sqlite3
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TestDatabase:
    """Test database with isolation support."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or ":memory:"
        self.connection: Optional[sqlite3.Connection] = None
        self._setup_scripts: List[str] = []
        self._teardown_scripts: List[str] = []
    
    async def setup(self) -> None:
        """Setup test database."""
        if self.db_path == ":memory:":
            self.connection = sqlite3.connect(":memory:")
        else:
            self.connection = sqlite3.connect(self.db_path)
        
        # Enable foreign keys
        self.connection.execute("PRAGMA foreign_keys = ON")
        
        # Run setup scripts
        for script in self._setup_scripts:
            self.connection.executescript(script)
        
        self.connection.commit()
        logger.debug(f"Test database setup complete: {self.db_path}")
    
    async def teardown(self) -> None:
        """Teardown test database."""
        if self.connection:
            # Run teardown scripts
            for script in self._teardown_scripts:
                self.connection.executescript(script)
            
            self.connection.close()
            self.connection = None
        
        # Remove file if it exists
        if self.db_path != ":memory:" and Path(self.db_path).exists():
            Path(self.db_path).unlink()
        
        logger.debug("Test database teardown complete")
    
    def add_setup_script(self, script: str) -> None:
        """Add SQL script to run during setup."""
        self._setup_scripts.append(script)
    
    def add_teardown_script(self, script: str) -> None:
        """Add SQL script to run during teardown."""
        self._teardown_scripts.append(script)
    
    def execute(self, sql: str, params: Optional[tuple] = None) -> Any:
        """Execute SQL query."""
        if not self.connection:
            raise RuntimeError("Database not initialized. Call setup() first.")
        
        cursor = self.connection.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        return cursor
    
    def execute_script(self, script: str) -> None:
        """Execute SQL script."""
        if not self.connection:
            raise RuntimeError("Database not initialized. Call setup() first.")
        
        self.connection.executescript(script)
        self.connection.commit()
    
    def fetch_one(self, sql: str, params: Optional[tuple] = None) -> Optional[tuple]:
        """Fetch single row."""
        cursor = self.execute(sql, params)
        return cursor.fetchone()
    
    def fetch_all(self, sql: str, params: Optional[tuple] = None) -> List[tuple]:
        """Fetch all rows."""
        cursor = self.execute(sql, params)
        return cursor.fetchall()
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Insert data into table."""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        cursor = self.execute(sql, tuple(data.values()))
        self.connection.commit()
        return cursor.lastrowid
    
    def update(self, table: str, data: Dict[str, Any], where: str, where_params: tuple) -> int:
        """Update data in table."""
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        params = tuple(data.values()) + where_params
        cursor = self.execute(sql, params)
        self.connection.commit()
        return cursor.rowcount
    
    def delete(self, table: str, where: str, where_params: tuple) -> int:
        """Delete data from table."""
        sql = f"DELETE FROM {table} WHERE {where}"
        
        cursor = self.execute(sql, where_params)
        self.connection.commit()
        return cursor.rowcount


class DatabaseTestUtils:
    """Utilities for database testing."""
    
    def __init__(self):
        self.databases: Dict[str, TestDatabase] = {}
    
    def create_database(self, name: str, db_path: Optional[str] = None) -> TestDatabase:
        """Create a new test database."""
        if db_path is None:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
            db_path = temp_file.name
            temp_file.close()
        
        db = TestDatabase(db_path)
        self.databases[name] = db
        return db
    
    def get_database(self, name: str) -> TestDatabase:
        """Get database by name."""
        if name not in self.databases:
            raise ValueError(f"Database '{name}' not found")
        return self.databases[name]
    
    def setup_all(self) -> None:
        """Setup all databases."""
        for name, db in self.databases.items():
            asyncio.create_task(db.setup())
            logger.debug(f"Setup database: {name}")
    
    def teardown_all(self) -> None:
        """Teardown all databases."""
        for name, db in self.databases.items():
            asyncio.create_task(db.teardown())
            logger.debug(f"Teardown database: {name}")
    
    def clear_all(self) -> None:
        """Clear all databases."""
        self.teardown_all()
        self.databases.clear()


# Common database schemas
USERS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
"""

POSTS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    author_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_published BOOLEAN DEFAULT 0,
    FOREIGN KEY (author_id) REFERENCES users (id)
);
"""

COMMENTS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    author_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    parent_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users (id),
    FOREIGN KEY (post_id) REFERENCES posts (id),
    FOREIGN KEY (parent_id) REFERENCES comments (id)
);
"""

PRODUCTS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category TEXT NOT NULL,
    in_stock INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


# Decorator for database test isolation
def with_database(db_name: str = "test_db"):
    """Decorator for database test isolation."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Create database utils
            db_utils = DatabaseTestUtils()
            db = db_utils.create_database(db_name)
            
            # Add common schemas
            db.add_setup_script(USERS_TABLE_SCHEMA)
            db.add_setup_script(POSTS_TABLE_SCHEMA)
            db.add_setup_script(COMMENTS_TABLE_SCHEMA)
            db.add_setup_script(PRODUCTS_TABLE_SCHEMA)
            
            try:
                # Setup database
                await db.setup()
                
                # Add database to kwargs
                kwargs['db'] = db
                kwargs['db_utils'] = db_utils
                
                # Run test
                result = await func(*args, **kwargs)
                
                return result
            finally:
                # Teardown database
                await db.teardown()
        
        return wrapper
    return decorator


# Context manager for database testing
@asynccontextmanager
async def test_database(db_name: str = "test_db", schemas: Optional[List[str]] = None):
    """Context manager for database testing."""
    db_utils = DatabaseTestUtils()
    db = db_utils.create_database(db_name)
    
    # Add schemas
    if schemas:
        for schema in schemas:
            db.add_setup_script(schema)
    
    try:
        await db.setup()
        yield db
    finally:
        await db.teardown() 