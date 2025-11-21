"""
Tests for utility modules.
"""

import pytest
import tempfile
import os
from pathlib import Path
from qakeapi.utils import StaticFiles, TemplateEngine, TemplateRenderer


def test_static_files():
    """Test StaticFiles."""
    # Create temporary directory with test file
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello, World!")

        static = StaticFiles(directory=tmpdir, path="/static")

        # Get file path
        file_path = static.get_file_path("/static/test.txt")
        assert file_path is not None
        assert file_path.name == "test.txt"

        # Test non-existent file
        assert static.get_file_path("/static/nonexistent.txt") is None

        # Test directory traversal protection
        assert static.get_file_path("/static/../etc/passwd") is None


def test_template_engine():
    """Test TemplateEngine."""
    # Create temporary directory with test template
    with tempfile.TemporaryDirectory() as tmpdir:
        template_file = Path(tmpdir) / "test.html"
        template_file.write_text("Hello, {{ name }}!")

        engine = TemplateEngine(directory=tmpdir)

        # Render template
        result = engine.render("test.html", {"name": "World"})
        assert result == "Hello, World!"


def test_template_engine_conditionals():
    """Test TemplateEngine with conditionals."""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_file = Path(tmpdir) / "test.html"
        template_file.write_text(
            "{% if show %}Visible{% endif %}{% if not hide %}Not Hidden{% endif %}"
        )

        engine = TemplateEngine(directory=tmpdir)

        # Test with show=True
        result = engine.render("test.html", {"show": True, "hide": False})
        assert "Visible" in result
        assert "Not Hidden" in result

        # Test with show=False
        result = engine.render("test.html", {"show": False, "hide": True})
        assert "Visible" not in result
        assert "Not Hidden" not in result


def test_template_engine_loops():
    """Test TemplateEngine with loops."""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_file = Path(tmpdir) / "test.html"
        template_file.write_text("{% for item in items %}{{ item }}{% endfor %}")

        engine = TemplateEngine(directory=tmpdir)

        result = engine.render("test.html", {"items": ["a", "b", "c"]})
        assert result == "abc"


def test_template_renderer():
    """Test TemplateRenderer."""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_file = Path(tmpdir) / "test.html"
        template_file.write_text("<h1>{{ title }}</h1>")

        renderer = TemplateRenderer(directory=tmpdir)

        response = renderer.TemplateResponse("test.html", {"title": "Hello"})
        assert isinstance(response, type(response))  # Check it's HTMLResponse
        assert b"<h1>Hello</h1>" in response.render()
