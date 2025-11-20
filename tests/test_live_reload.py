"""
Tests for live reload functionality in QakeAPI.
"""
import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from qakeapi.templates.live_reload import (
    LiveReloadManager,
    LiveReloadMiddleware,
    TemplateChangeHandler,
    setup_live_reload,
    start_live_reload,
    stop_live_reload,
    add_live_reload_callback,
    remove_live_reload_callback,
    get_live_reload_manager,
)
from qakeapi.templates import Jinja2TemplateEngine, render_template


class TestTemplateChangeHandler:
    """Test template change handler."""

    def test_is_template_file(self):
        """Test template file detection."""
        handler = TemplateChangeHandler(Mock())

        # Valid template files
        assert handler._is_template_file("template.html")
        assert handler._is_template_file("page.htm")
        assert handler._is_template_file("layout.jinja")
        assert handler._is_template_file("form.jinja2")
        assert handler._is_template_file("email.j2")
        assert handler._is_template_file("sitemap.xml")
        assert handler._is_template_file("readme.txt")

        # Invalid files
        assert not handler._is_template_file("script.js")
        assert not handler._is_template_file("style.css")
        assert not handler._is_template_file("image.png")
        assert not handler._is_template_file("data.json")

    def test_debounce_functionality(self):
        """Test debouncing of rapid file changes."""
        callback = Mock()
        handler = TemplateChangeHandler(callback)

        # Simulate rapid file changes
        handler.on_modified(Mock(src_path="test.html", is_directory=False))
        handler.on_modified(Mock(src_path="test.html", is_directory=False))

        # Should only call callback once due to debouncing
        assert callback.call_count == 1


class TestLiveReloadManager:
    """Test live reload manager."""

    def setup_method(self):
        """Setup test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = LiveReloadManager([self.temp_dir], enabled=False)

    def teardown_method(self):
        """Teardown test method."""
        if self.manager:
            self.manager.stop()

    def test_initialization(self):
        """Test manager initialization."""
        assert self.manager.template_dirs == [Path(self.temp_dir)]
        assert self.manager.enabled is False
        assert len(self.manager.callbacks) == 0

    def test_add_remove_callback(self):
        """Test adding and removing callbacks."""
        callback1 = Mock()
        callback1.__name__ = "test_callback1"
        callback2 = Mock()
        callback2.__name__ = "test_callback2"

        # Add callbacks
        self.manager.add_callback(callback1)
        self.manager.add_callback(callback2)

        assert len(self.manager.callbacks) == 2
        assert callback1 in self.manager.callbacks
        assert callback2 in self.manager.callbacks

        # Remove callback
        self.manager.remove_callback(callback1)
        assert len(self.manager.callbacks) == 1
        assert callback1 not in self.manager.callbacks
        assert callback2 in self.manager.callbacks

    def test_watched_files_management(self):
        """Test watched files management."""
        file1 = "template1.html"
        file2 = "template2.html"

        # Add files to watch
        self.manager.add_watch_file(file1)
        self.manager.add_watch_file(file2)

        watched_files = self.manager.get_watched_files()
        assert file1 in watched_files
        assert file2 in watched_files

        # Remove file from watch
        self.manager.remove_watch_file(file1)
        watched_files = self.manager.get_watched_files()
        assert file1 not in watched_files
        assert file2 in watched_files


class TestLiveReloadMiddleware:
    """Test live reload middleware."""

    def setup_method(self):
        """Setup test method."""
        self.middleware = LiveReloadMiddleware(enabled=True, port=35729)

    @pytest.mark.asyncio
    async def test_html_injection(self):
        """Test HTML injection with live reload script."""
        # Mock request and response
        request = Mock()
        response = Mock()
        response.headers = {b"content-type": b"text/html; charset=utf-8"}
        response.content = b"<html><body>Hello</body></html>"

        # Mock handler
        async def handler(req):
            return response

        # Process through middleware
        result = await self.middleware(request, handler)

        # Check if live reload script was injected
        content = result.content.decode("utf-8")
        assert "livereload.js" in content
        assert "localhost:35729" in content

    @pytest.mark.asyncio
    async def test_non_html_response(self):
        """Test that non-HTML responses are not modified."""
        # Mock request and response
        request = Mock()
        response = Mock()
        response.headers = {b"content-type": b"application/json"}
        response.content = b'{"key": "value"}'

        # Mock handler
        async def handler(req):
            return response

        # Process through middleware
        result = await self.middleware(request, handler)

        # Content should not be modified
        assert result.content == b'{"key": "value"}'

    @pytest.mark.asyncio
    async def test_disabled_middleware(self):
        """Test disabled middleware."""
        middleware = LiveReloadMiddleware(enabled=False)

        # Mock request and response
        request = Mock()
        response = Mock()
        response.headers = {b"content-type": b"text/html; charset=utf-8"}
        response.content = b"<html><body>Hello</body></html>"

        # Mock handler
        async def handler(req):
            return response

        # Process through middleware
        result = await middleware(request, handler)

        # Content should not be modified
        assert result.content == b"<html><body>Hello</body></html>"


class TestGlobalLiveReloadFunctions:
    """Test global live reload functions."""

    def setup_method(self):
        """Setup test method."""
        # Clean up any existing manager
        stop_live_reload()

    def teardown_method(self):
        """Teardown test method."""
        stop_live_reload()

    def test_setup_live_reload(self):
        """Test setting up live reload."""
        temp_dir = tempfile.mkdtemp()
        manager = setup_live_reload([temp_dir], enabled=False)

        assert manager is not None
        assert manager.template_dirs == [Path(temp_dir)]
        assert manager.enabled is False

        # Check global instance
        global_manager = get_live_reload_manager()
        assert global_manager is manager

    def test_start_stop_live_reload(self):
        """Test starting and stopping live reload."""
        temp_dir = tempfile.mkdtemp()
        setup_live_reload([temp_dir], enabled=False)

        # Start and stop should not raise errors
        start_live_reload()
        stop_live_reload()

    def test_callback_management(self):
        """Test callback management functions."""
        temp_dir = tempfile.mkdtemp()
        setup_live_reload([temp_dir], enabled=False)

        callback1 = Mock()
        callback1.__name__ = "test_callback1"
        callback2 = Mock()
        callback2.__name__ = "test_callback2"

        # Add callbacks
        add_live_reload_callback(callback1)
        add_live_reload_callback(callback2)

        manager = get_live_reload_manager()
        assert len(manager.callbacks) == 2

        # Remove callback
        remove_live_reload_callback(callback1)
        assert len(manager.callbacks) == 1
        assert callback1 not in manager.callbacks
        assert callback2 in manager.callbacks


class TestJinja2TemplateEngineLiveReload:
    """Test Jinja2 template engine with live reload."""

    def setup_method(self):
        """Setup test method."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Teardown test method."""
        # Clean up
        stop_live_reload()

    def test_live_reload_enabled(self):
        """Test template engine with live reload enabled."""
        # Create template engine with live reload
        engine = Jinja2TemplateEngine(template_dir=self.temp_dir, live_reload=True)

        # Check that live reload was enabled
        assert engine.live_reload_enabled is True

        # Cleanup
        engine.stop_live_reload()

    def test_live_reload_disabled(self):
        """Test template engine with live reload disabled."""
        # Create template engine without live reload
        engine = Jinja2TemplateEngine(template_dir=self.temp_dir, live_reload=False)

        # Check that live reload was not enabled
        assert engine.live_reload_enabled is False

    def test_stop_live_reload(self):
        """Test stopping live reload."""
        # Create template engine with live reload
        engine = Jinja2TemplateEngine(template_dir=self.temp_dir, live_reload=True)

        # Stop live reload
        engine.stop_live_reload()

        # Check that live reload was disabled
        assert engine.live_reload_enabled is False


class TestRenderTemplateLiveReload:
    """Test render_template function with live reload."""

    def setup_method(self):
        """Setup test method."""
        self.temp_dir = tempfile.mkdtemp()

        # Create a test template
        template_path = Path(self.temp_dir) / "test.html"
        template_path.write_text("Hello {{ name }}!")

    def teardown_method(self):
        """Teardown test method."""
        stop_live_reload()

    def test_render_template_with_live_reload(self):
        """Test rendering template with live reload enabled."""
        # Create a test template
        template_path = Path(self.temp_dir) / "test.html"
        template_path.write_text("Hello {{ name }}!")

        # Render template with live reload
        response = render_template(
            "test.html",
            {"name": "World"},
            template_engine=Jinja2TemplateEngine(
                template_dir=self.temp_dir, live_reload=True
            ),
        )

        # Check response
        assert response.status_code == 200
        assert "Hello World!" in response.content
        assert any(
            k == b"content-type" and b"text/html" in v for k, v in response.headers
        )

    def test_render_template_without_live_reload(self):
        """Test rendering template without live reload."""
        # Create a test template
        template_path = Path(self.temp_dir) / "test.html"
        template_path.write_text("Hello {{ name }}!")

        # Render template without live reload
        response = render_template(
            "test.html",
            {"name": "World"},
            template_engine=Jinja2TemplateEngine(
                template_dir=self.temp_dir, live_reload=False
            ),
        )

        # Check response
        assert response.status_code == 200
        assert "Hello World!" in response.content
        assert any(
            k == b"content-type" and b"text/html" in v for k, v in response.headers
        )


# Integration tests
class TestLiveReloadIntegration:
    """Integration tests for live reload functionality."""

    def setup_method(self):
        """Setup test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.template_dir = Path(self.temp_dir) / "templates"
        self.template_dir.mkdir()

    def teardown_method(self):
        """Teardown test method."""
        stop_live_reload()

    def test_full_live_reload_workflow(self):
        """Test complete live reload workflow."""
        # Create template file
        template_file = self.template_dir / "index.html"
        template_file.write_text("Hello {{ name }}!")

        # Setup live reload
        manager = setup_live_reload([str(self.template_dir)], enabled=True)

        # Add callback
        callback_called = False

        def on_template_change(file_path):
            nonlocal callback_called
            callback_called = True

        manager.add_callback(on_template_change)

        # Simulate template change
        manager._on_template_change(str(template_file))

        # Check that callback was called
        assert callback_called is True

    def test_template_engine_with_file_changes(self):
        """Test template engine with actual file changes."""
        # Create template file
        template_file = self.template_dir / "dynamic.html"
        template_file.write_text("Current time: {{ time }}")

        # Create template engine with live reload
        engine = Jinja2TemplateEngine(
            template_dir=str(self.template_dir), live_reload=True
        )

        # Render template
        content = engine.render("dynamic.html", {"time": "12:00"})
        assert "Current time: 12:00" in content

        # Modify template file
        template_file.write_text("Updated time: {{ time }}")

        # Render again (should use updated template)
        content = engine.render("dynamic.html", {"time": "13:00"})
        assert "Updated time: 13:00" in content

        # Cleanup
        engine.stop_live_reload()
