"""
Тесты для утилит QakeAPI
"""
import pytest
import os
import tempfile
from pathlib import Path
from qakeapi.utils.status import HTTPStatus, status
from qakeapi.utils.static import StaticFiles
from qakeapi.utils.templates import SimpleTemplates


class TestHTTPStatus:
    """Тесты HTTP статус кодов"""
    
    def test_status_codes(self):
        """Тест основных статус кодов"""
        assert HTTPStatus.OK == 200
        assert HTTPStatus.NOT_FOUND == 404
        assert HTTPStatus.INTERNAL_SERVER_ERROR == 500
        assert HTTPStatus.BAD_REQUEST == 400
        assert HTTPStatus.UNAUTHORIZED == 401
        assert HTTPStatus.FORBIDDEN == 403
        
        # Проверяем экземпляр
        assert status.OK == 200
        assert status.CREATED == 201
        assert status.NO_CONTENT == 204
    
    def test_informational_codes(self):
        """Тест информационных кодов 1xx"""
        assert HTTPStatus.CONTINUE == 100
        assert HTTPStatus.SWITCHING_PROTOCOLS == 101
    
    def test_success_codes(self):
        """Тест кодов успеха 2xx"""
        assert HTTPStatus.OK == 200
        assert HTTPStatus.CREATED == 201
        assert HTTPStatus.ACCEPTED == 202
        assert HTTPStatus.NO_CONTENT == 204
    
    def test_redirection_codes(self):
        """Тест кодов перенаправления 3xx"""
        assert HTTPStatus.MOVED_PERMANENTLY == 301
        assert HTTPStatus.FOUND == 302
        assert HTTPStatus.NOT_MODIFIED == 304
        assert HTTPStatus.TEMPORARY_REDIRECT == 307
    
    def test_client_error_codes(self):
        """Тест кодов ошибок клиента 4xx"""
        assert HTTPStatus.BAD_REQUEST == 400
        assert HTTPStatus.UNAUTHORIZED == 401
        assert HTTPStatus.FORBIDDEN == 403
        assert HTTPStatus.NOT_FOUND == 404
        assert HTTPStatus.METHOD_NOT_ALLOWED == 405
        assert HTTPStatus.UNPROCESSABLE_ENTITY == 422
        assert HTTPStatus.TOO_MANY_REQUESTS == 429
    
    def test_server_error_codes(self):
        """Тест кодов ошибок сервера 5xx"""
        assert HTTPStatus.INTERNAL_SERVER_ERROR == 500
        assert HTTPStatus.NOT_IMPLEMENTED == 501
        assert HTTPStatus.BAD_GATEWAY == 502
        assert HTTPStatus.SERVICE_UNAVAILABLE == 503


class TestStaticFiles:
    """Тесты для обслуживания статических файлов"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.temp_dir = tempfile.mkdtemp()
        self.static_dir = Path(self.temp_dir) / "static"
        self.static_dir.mkdir()
        
        # Создаем тестовые файлы
        (self.static_dir / "test.txt").write_text("Hello, World!", encoding="utf-8")
        (self.static_dir / "style.css").write_text("body { color: red; }", encoding="utf-8")
        (self.static_dir / "script.js").write_text("console.log('Hello');", encoding="utf-8")
        (self.static_dir / "image.png").write_bytes(b"fake-png-data")
        
        # Создаем скрытый файл
        (self.static_dir / ".hidden").write_text("secret", encoding="utf-8")
        
        # Создаем поддиректорию
        subdir = self.static_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("Nested file", encoding="utf-8")
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_static_files_creation(self):
        """Тест создания StaticFiles"""
        static_files = StaticFiles(directory=str(self.static_dir))
        assert static_files.directory == self.static_dir.resolve()
    
    def test_nonexistent_directory(self):
        """Тест с несуществующей директорией"""
        with pytest.raises(RuntimeError, match="does not exist|is not a directory"):
            StaticFiles(directory="/nonexistent/path")
    
    def test_get_file_path(self):
        """Тест получения пути к файлу"""
        static_files = StaticFiles(directory=str(self.static_dir))
        
        # Существующий файл
        file_path = static_files._get_file_path("test.txt")
        assert file_path is not None
        assert file_path.name == "test.txt"
        
        # Несуществующий файл
        file_path = static_files._get_file_path("nonexistent.txt")
        assert file_path is None
        
        # Попытка выйти за пределы директории
        file_path = static_files._get_file_path("../../../etc/passwd")
        assert file_path is None
        
        # Файл в поддиректории
        file_path = static_files._get_file_path("subdir/nested.txt")
        assert file_path is not None
        assert file_path.name == "nested.txt"
    
    def test_get_media_type(self):
        """Тест определения MIME типа"""
        static_files = StaticFiles(directory=str(self.static_dir))
        
        test_cases = [
            ("test.txt", "text/plain"),
            ("style.css", "text/css"),
            ("script.js", "application/javascript"),
            ("image.png", "image/png"),
            ("unknown.xyz", "application/octet-stream"),
        ]
        
        for filename, expected_type in test_cases:
            file_path = self.static_dir / filename
            media_type = static_files._get_media_type(file_path)
            assert media_type == expected_type
    
    def test_should_serve_file(self):
        """Тест проверки возможности обслуживания файла"""
        static_files = StaticFiles(directory=str(self.static_dir))
        
        # Обычные файлы должны обслуживаться
        assert static_files._should_serve_file(self.static_dir / "test.txt")
        assert static_files._should_serve_file(self.static_dir / "style.css")
        
        # Скрытые файлы не должны обслуживаться
        assert not static_files._should_serve_file(self.static_dir / ".hidden")
    
    def test_html_serving(self):
        """Тест обслуживания HTML файлов"""
        # Создаем HTML файл
        (self.static_dir / "index.html").write_text("<html><body>Test</body></html>")
        
        # По умолчанию HTML не обслуживается
        static_files = StaticFiles(directory=str(self.static_dir))
        assert not static_files._should_serve_file(self.static_dir / "index.html")
        
        # С включенным HTML
        static_files = StaticFiles(directory=str(self.static_dir), html=True)
        assert static_files._should_serve_file(self.static_dir / "index.html")


class TestSimpleTemplates:
    """Тесты для простых шаблонов"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.temp_dir = tempfile.mkdtemp()
        self.templates_dir = Path(self.temp_dir) / "templates"
        self.templates_dir.mkdir()
        
        # Создаем тестовые шаблоны
        (self.templates_dir / "simple.html").write_text(
            "<html><body><h1>{title}</h1><p>{content}</p></body></html>",
            encoding="utf-8"
        )
        
        (self.templates_dir / "no_vars.html").write_text(
            "<html><body><h1>Static Template</h1></body></html>",
            encoding="utf-8"
        )
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_templates_creation(self):
        """Тест создания SimpleTemplates"""
        templates = SimpleTemplates(directory=str(self.templates_dir))
        assert templates.directory == self.templates_dir
    
    def test_nonexistent_directory(self):
        """Тест с несуществующей директорией шаблонов"""
        from qakeapi.core.exceptions import QakeAPIException
        
        with pytest.raises(QakeAPIException, match="does not exist"):
            SimpleTemplates(directory="/nonexistent/templates")
    
    def test_render_template(self):
        """Тест рендеринга шаблона"""
        templates = SimpleTemplates(directory=str(self.templates_dir))
        
        # Рендеринг с переменными
        result = templates.render("simple.html", {
            "title": "Test Title",
            "content": "Test Content"
        })
        
        assert "Test Title" in result
        assert "Test Content" in result
        assert "<html>" in result
    
    def test_render_without_variables(self):
        """Тест рендеринга без переменных"""
        templates = SimpleTemplates(directory=str(self.templates_dir))
        
        result = templates.render("no_vars.html")
        assert "Static Template" in result
    
    def test_missing_template(self):
        """Тест с отсутствующим шаблоном"""
        from qakeapi.core.exceptions import QakeAPIException
        
        templates = SimpleTemplates(directory=str(self.templates_dir))
        
        with pytest.raises(QakeAPIException, match="not found"):
            templates.render("nonexistent.html")
    
    def test_missing_variable(self):
        """Тест с отсутствующей переменной"""
        from qakeapi.core.exceptions import QakeAPIException
        
        templates = SimpleTemplates(directory=str(self.templates_dir))
        
        with pytest.raises(QakeAPIException, match="Missing template variable"):
            templates.render("simple.html", {"title": "Only Title"})  # content отсутствует
    
    def test_template_response(self):
        """Тест создания TemplateResponse"""
        templates = SimpleTemplates(directory=str(self.templates_dir))
        
        response = templates.TemplateResponse("simple.html", {
            "title": "Response Title",
            "content": "Response Content"
        })
        
        assert response.status_code == 200
        assert "text/html" in response.media_type
        assert "Response Title" in response.content
        assert "Response Content" in response.content
    
    def test_template_response_with_status(self):
        """Тест TemplateResponse с кастомным статусом"""
        templates = SimpleTemplates(directory=str(self.templates_dir))
        
        response = templates.TemplateResponse(
            "no_vars.html",
            status_code=201,
            headers={"X-Custom": "value"}
        )
        
        assert response.status_code == 201
        assert response.headers["X-Custom"] == "value"


class TestPathSecurity:
    """Тесты безопасности путей"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.temp_dir = tempfile.mkdtemp()
        self.safe_dir = Path(self.temp_dir) / "safe"
        self.safe_dir.mkdir()
        
        # Создаем файл в безопасной директории
        (self.safe_dir / "safe.txt").write_text("Safe content")
        
        # Создаем файл вне безопасной директории
        (Path(self.temp_dir) / "unsafe.txt").write_text("Unsafe content")
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_path_traversal_protection(self):
        """Тест защиты от path traversal атак"""
        static_files = StaticFiles(directory=str(self.safe_dir))
        
        # Попытки выйти за пределы директории
        dangerous_paths = [
            "../unsafe.txt",
            "../../etc/passwd",
            "../../../windows/system32/config/sam",
            "..\\..\\windows\\system32\\config\\sam",  # Windows style
            "/etc/passwd",  # Absolute path
            "\\windows\\system32\\config\\sam",  # Windows absolute
        ]
        
        for dangerous_path in dangerous_paths:
            file_path = static_files._get_file_path(dangerous_path)
            assert file_path is None, f"Path traversal should be blocked: {dangerous_path}"
    
    def test_safe_paths(self):
        """Тест безопасных путей"""
        static_files = StaticFiles(directory=str(self.safe_dir))
        
        safe_paths = [
            "safe.txt",
            "./safe.txt",
            "subdir/../safe.txt",  # Разрешено, если результат в пределах директории
        ]
        
        for safe_path in safe_paths:
            if safe_path == "safe.txt" or safe_path == "./safe.txt":
                file_path = static_files._get_file_path(safe_path)
                assert file_path is not None, f"Safe path should be allowed: {safe_path}"
