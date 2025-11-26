"""
Tests for CORS middleware methods.
"""

import pytest
from qakeapi.core.middleware import CORSMiddleware


class TestCORSMiddlewareMethods:
    """Tests for CORS middleware helper methods."""
    
    def test_extract_origin_from_origin_header(self):
        """Test extracting origin from origin header."""
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers
        
        middleware = CORSMiddleware()
        request = MockRequest({"origin": "https://example.com"})
        
        origin = middleware._extract_origin(request)
        assert origin == "https://example.com"
    
    def test_extract_origin_from_referer(self):
        """Test extracting origin from referer header."""
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers
        
        middleware = CORSMiddleware()
        request = MockRequest({"referer": "https://example.com/page"})
        
        origin = middleware._extract_origin(request)
        assert origin == "https://example.com"
    
    def test_get_allow_origin_wildcard(self):
        """Test getting allow origin with wildcard."""
        middleware = CORSMiddleware(allow_origins=["*"])
        
        assert middleware._get_allow_origin("https://example.com") == "https://example.com"
        assert middleware._get_allow_origin("") == "*"
    
    def test_get_allow_origin_allowed_list(self):
        """Test getting allow origin from allowed list."""
        middleware = CORSMiddleware(allow_origins=["https://example.com", "https://test.com"])
        
        assert middleware._get_allow_origin("https://example.com") == "https://example.com"
        assert middleware._get_allow_origin("https://unauthorized.com") == "*"
        assert middleware._get_allow_origin("") == "*"
    
    def test_get_allow_methods_wildcard(self):
        """Test getting allow methods with wildcard."""
        middleware = CORSMiddleware(allow_methods=["*"])
        
        methods = middleware._get_allow_methods()
        assert "GET" in methods
        assert "POST" in methods
        assert "OPTIONS" in methods
    
    def test_get_allow_methods_specific(self):
        """Test getting allow methods with specific methods."""
        middleware = CORSMiddleware(allow_methods=["GET", "POST"])
        
        methods = middleware._get_allow_methods()
        assert "GET" in methods
        assert "POST" in methods
        assert "OPTIONS" in methods  # Should be added automatically
    
    def test_get_allow_headers_wildcard(self):
        """Test getting allow headers with wildcard."""
        middleware = CORSMiddleware(allow_headers=["*"])
        
        headers = middleware._get_allow_headers()
        assert "Content-Type" in headers
        assert "Authorization" in headers
    
    def test_get_allow_headers_specific(self):
        """Test getting allow headers with specific headers."""
        middleware = CORSMiddleware(allow_headers=["X-Custom"])
        
        headers = middleware._get_allow_headers()
        assert "X-Custom" in headers
        assert "Content-Type" in headers  # Should be added automatically
        assert "Accept" in headers  # Should be added automatically

