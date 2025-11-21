"""
Tests for template system.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from qakeapi.templates.jinja2 import (
    Jinja2TemplateEngine,
    TemplateEngine,
    render_template,
    render_template_string,
)
from qakeapi.templates.renderers import (
    TemplateCache,
    CachedTemplateEngine,
    TemplateDebugger,
    create_template_engine,
)


class TestTemplateEngine:
    """Test abstract template engine."""

    def test_template_engine_abstract(self):
        """Test that TemplateEngine is abstract."""
        with pytest.raises(TypeError):
            TemplateEngine()


class TestJinja2TemplateEngine:
    """Test Jinja2 template engine."""

    def test_init_without_jinja2(self):
        """Test initialization without Jinja2 installed."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", False):
            with pytest.raises(ImportError):
                Jinja2TemplateEngine()

    def test_init_with_jinja2(self):
        """Test initialization with Jinja2 available."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", True):
            engine = Jinja2TemplateEngine()
            assert engine.template_dir.exists()

    def test_render_string(self):
        """Test rendering template string."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", True):
            engine = Jinja2TemplateEngine()
            result = engine.render_string("Hello {{ name }}!", {"name": "World"})
            assert result == "Hello World!"

    def test_add_filter(self):
        """Test adding custom filter."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", True):
            engine = Jinja2TemplateEngine()

            def upper_filter(value):
                return value.upper()

            engine.add_filter("upper", upper_filter)
            result = engine.render_string("{{ name | upper }}", {"name": "hello"})
            assert result == "HELLO"

    def test_add_function(self):
        """Test adding custom function."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", True):
            engine = Jinja2TemplateEngine()

            def greet(name):
                return f"Hello {name}!"

            engine.add_function("greet", greet)
            result = engine.render_string("{{ greet(name) }}", {"name": "World"})
            assert result == "Hello World!"


class TestTemplateCache:
    """Test template caching."""

    def test_cache_get_set(self):
        """Test basic cache operations."""
        cache = TemplateCache(max_size=10)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None

    def test_cache_max_size(self):
        """Test cache size limit."""
        cache = TemplateCache(max_size=2)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = TemplateCache()
        cache.set("key1", "value1")
        cache.clear()
        assert cache.get("key1") is None


class TestCachedTemplateEngine:
    """Test cached template engine."""

    def test_cached_render(self):
        """Test template rendering with cache."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", True):
            engine = CachedTemplateEngine(enable_cache=True)

            # First render should cache
            result1 = engine.render_string("Hello {{ name }}!", {"name": "World"})
            assert result1 == "Hello World!"

            # Second render should use cache
            result2 = engine.render_string("Hello {{ name }}!", {"name": "World"})
            assert result2 == "Hello World!"

    def test_cache_disabled(self):
        """Test template engine with cache disabled."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", True):
            engine = CachedTemplateEngine(enable_cache=False)
            assert engine.cache is None


class TestTemplateDebugger:
    """Test template debugging."""

    def test_debug_render(self):
        """Test debug rendering."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", True):
            engine = Jinja2TemplateEngine()
            debugger = TemplateDebugger(engine)

            # Use render_string instead of render to avoid file dependency
            result = debugger.debug_render_string(
                "Hello {{ name }}!", {"name": "World"}
            )
            assert result == "Hello World!"

    def test_get_stats(self):
        """Test getting debug statistics."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", True):
            engine = Jinja2TemplateEngine()
            debugger = TemplateDebugger(engine)

            debugger.debug_render_string("Hello {{ name }}!", {"name": "World"})
            stats = debugger.get_stats()

            assert "Hello {{ name }}!" in stats
            assert stats["Hello {{ name }}!"]["render_count"] == 1

    def test_reset_stats(self):
        """Test resetting debug statistics."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", True):
            engine = Jinja2TemplateEngine()
            debugger = TemplateDebugger(engine)

            debugger.debug_render_string("Hello {{ name }}!", {"name": "World"})
            debugger.reset_stats()

            assert not debugger.render_stats


class TestRenderFunctions:
    """Test render helper functions."""

    def test_render_template_string(self):
        """Test render_template_string function."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", True):
            response = render_template_string("Hello {{ name }}!", {"name": "World"})

            assert response.status_code == 200
            # Check content as string, not bytes
            if isinstance(response.content, bytes):
                content = response.content.decode()
            else:
                content = str(response.content)
            assert "Hello World!" in content
            assert b"text/html" in response.headers[0][1]

    def test_render_template_string_with_headers(self):
        """Test render_template_string with custom headers."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", True):
            response = render_template_string(
                "Hello {{ name }}!", {"name": "World"}, headers={"X-Custom": "value"}
            )

            assert response.status_code == 200
            assert any(b"X-Custom" in header[0] for header in response.headers)


class TestCreateTemplateEngine:
    """Test template engine factory."""

    def test_create_basic_engine(self):
        """Test creating basic template engine."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", True):
            engine = create_template_engine(enable_cache=False)
            assert isinstance(engine, Jinja2TemplateEngine)
            assert not hasattr(engine, "cache")

    def test_create_cached_engine(self):
        """Test creating cached template engine."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", True):
            engine = create_template_engine(enable_cache=True)
            assert isinstance(engine, CachedTemplateEngine)
            assert engine.cache is not None

    def test_create_debug_engine(self):
        """Test creating debug template engine."""
        with patch("qakeapi.templates.jinja2.JINJA2_AVAILABLE", True):
            engine = create_template_engine(enable_debug=True)
            assert hasattr(engine, "debugger")
            assert isinstance(engine.debugger, TemplateDebugger)


@pytest.mark.asyncio
async def test_template_debug_decorator():
    """Test template debug decorator."""
    from qakeapi.templates.renderers import template_debug

    @template_debug
    async def test_function():
        return "test"

    result = await test_function()
    assert result == "test"
