"""
Tests for OpenAPI documentation generation.
"""

import pytest
from qakeapi.core.openapi import OpenAPIGenerator


class TestOpenAPIGenerator:
    """Tests for OpenAPIGenerator."""
    
    def test_generator_creation(self):
        """Test OpenAPI generator creation."""
        generator = OpenAPIGenerator(
            title="Test API",
            version="1.0.0",
            description="Test API description",
        )
        
        assert generator.title == "Test API"
        assert generator.version == "1.0.0"
        assert generator.description == "Test API description"
    
    def test_add_route(self):
        """Test adding route to generator."""
        generator = OpenAPIGenerator()
        
        def get_user(id: int):
            """Get user by ID."""
            return {"id": id}
        
        generator.add_route("/users/{id}", "GET", get_user)
        
        assert len(generator.routes) == 1
    
    def test_generate_spec(self):
        """Test generating OpenAPI specification."""
        generator = OpenAPIGenerator(
            title="Test API",
            version="1.0.0",
        )
        
        def get_user(id: int):
            """Get user by ID."""
            return {"id": id}
        
        def create_user(name: str):
            """Create user."""
            return {"name": name}
        
        generator.add_route("/users/{id}", "GET", get_user)
        generator.add_route("/users", "POST", create_user)
        
        spec = generator.generate_spec()
        
        assert spec["openapi"] == "3.0.0"
        assert spec["info"]["title"] == "Test API"
        assert spec["info"]["version"] == "1.0.0"
        assert "paths" in spec
        assert "/users/{id}" in spec["paths"]
        assert "/users" in spec["paths"]
        assert "get" in spec["paths"]["/users/{id}"]
        assert "post" in spec["paths"]["/users"]
    
    def test_generate_spec_with_parameters(self):
        """Test generating spec with path parameters."""
        generator = OpenAPIGenerator()
        
        def get_user(id: int, limit: int = 10):
            """Get user."""
            return {"id": id, "limit": limit}
        
        generator.add_route("/users/{id}", "GET", get_user)
        
        spec = generator.generate_spec()
        
        path_spec = spec["paths"]["/users/{id}"]["get"]
        assert "parameters" in path_spec
        
        # Check path parameter
        path_params = [p for p in path_spec["parameters"] if p["in"] == "path"]
        assert len(path_params) > 0
        assert path_params[0]["name"] == "id"
        
        # Check query parameter
        query_params = [p for p in path_spec["parameters"] if p["in"] == "query"]
        assert len(query_params) > 0
        assert query_params[0]["name"] == "limit"


