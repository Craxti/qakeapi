"""SQL injection protection module."""
import re
from typing import Any, Dict, List, Optional, Union

class SQLProtection:
    """SQL injection protection class."""
    
    @staticmethod
    def sanitize_input(value: Any) -> str:
        """Sanitize input to prevent SQL injection."""
        if value is None:
            return "NULL"
        
        if isinstance(value, (int, float)):
            return str(value)
        
        # Escape special characters
        if isinstance(value, str):
            value = value.replace("'", "''")
            value = value.replace("\\", "\\\\")
            return f"'{value}'"
        
        raise ValueError(f"Unsupported type for SQL sanitization: {type(value)}")
    
    @staticmethod
    def validate_table_name(table_name: str) -> bool:
        """Validate table name to prevent SQL injection."""
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, table_name))
    
    @staticmethod
    def validate_column_name(column_name: str) -> bool:
        """Validate column name to prevent SQL injection."""
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, column_name))
    
    @classmethod
    def build_safe_query(cls, 
                        query_type: str,
                        table: str,
                        columns: Optional[List[str]] = None,
                        values: Optional[Union[List[Any], Dict[str, Any]]] = None,
                        where: Optional[Dict[str, Any]] = None) -> str:
        """Build a safe SQL query with sanitized inputs."""
        if not cls.validate_table_name(table):
            raise ValueError(f"Invalid table name: {table}")
            
        if columns:
            for col in columns:
                if not cls.validate_column_name(col):
                    raise ValueError(f"Invalid column name: {col}")
        
        query = ""
        if query_type.upper() == "SELECT":
            cols = "*" if not columns else ", ".join(columns)
            query = f"SELECT {cols} FROM {table}"
            
        elif query_type.upper() == "INSERT":
            if not values:
                raise ValueError("Values required for INSERT")
                
            if isinstance(values, dict):
                cols = ", ".join(values.keys())
                vals = ", ".join(cls.sanitize_input(v) for v in values.values())
                query = f"INSERT INTO {table} ({cols}) VALUES ({vals})"
                
            elif isinstance(values, list):
                if not columns:
                    raise ValueError("Columns required for INSERT with value list")
                cols = ", ".join(columns)
                vals = ", ".join(cls.sanitize_input(v) for v in values)
                query = f"INSERT INTO {table} ({cols}) VALUES ({vals})"
        
        if where:
            conditions = []
            for col, val in where.items():
                if not cls.validate_column_name(col):
                    raise ValueError(f"Invalid column name in WHERE clause: {col}")
                conditions.append(f"{col} = {cls.sanitize_input(val)}")
            query += " WHERE " + " AND ".join(conditions)
        
        return query 