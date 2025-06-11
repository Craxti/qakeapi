import pytest
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response
from qakeapi.core.files import UploadFile
from http.cookies import SimpleCookie
import os
import tempfile

class TestRequest:
    def test_request_properties(self):
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "query_string": b"foo=bar&foo=baz",
            "headers": [
                (b"content-type", b"application/json"),
                (b"cookie", b"session=abc123; user=john")
            ],
            "client": ("127.0.0.1", 8000),
            "server": ("localhost", 8000),
            "scheme": "http"
        }
        body = b'{"hello": "world"}'
        request = Request(scope, body)
        
        assert request.method == "GET"
        assert request.path == "/test"
        assert request.query_params == {"foo": ["bar", "baz"]}
        assert request.headers == {
            b"content-type": b"application/json",
            b"cookie": b"session=abc123; user=john"
        }
        assert request.content_type == "application/json"
        assert request.body == body
        assert request.client == ("127.0.0.1", 8000)
        assert request.url == "http://localhost:8000/test?foo=bar&foo=baz"
        
    @pytest.mark.asyncio
    async def test_request_json(self):
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [(b"content-type", b"application/json")]
        }
        body = b'{"hello": "world"}'
        request = Request(scope, body)
        
        json_data = await request.json()
        assert json_data == {"hello": "world"}
        
    @pytest.mark.asyncio
    async def test_request_form(self):
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [(b"content-type", b"application/x-www-form-urlencoded")]
        }
        body = b"foo=bar&foo=baz"
        request = Request(scope, body)
        
        form_data = await request.form()
        assert form_data == {"foo": ["bar", "baz"]}
        
    def test_request_cookies(self):
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [(b"cookie", b"session=abc123; user=john")]
        }
        request = Request(scope)
        
        assert isinstance(request.cookies, SimpleCookie)
        assert request.cookies["session"].value == "abc123"
        assert request.cookies["user"].value == "john"

    @pytest.mark.asyncio
    async def test_request_file_upload(self):
        # Создаем multipart/form-data запрос
        boundary = "boundary"
        body = (
            f'--{boundary}\r\n'
            'Content-Disposition: form-data; name="file1"; filename="test.txt"\r\n'
            'Content-Type: text/plain\r\n'
            '\r\n'
            'Hello, World!\r\n'
            f'--{boundary}\r\n'
            'Content-Disposition: form-data; name="field1"\r\n'
            '\r\n'
            'value1\r\n'
            f'--{boundary}\r\n'
            'Content-Disposition: form-data; name="file2"; filename="image.jpg"\r\n'
            'Content-Type: image/jpeg\r\n'
            '\r\n'
            'binary data\r\n'
            f'--{boundary}--\r\n'
        ).encode()
        
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/upload",
            "headers": [(b"content-type", f"multipart/form-data; boundary={boundary}".encode())]
        }
        
        request = Request(scope, body)
        
        # Проверяем форму
        form = await request.form()
        assert form["field1"] == "value1"
        
        # Проверяем файлы
        files = await request.files()
        assert len(files) == 2
        
        # Проверяем первый файл
        file1 = files["file1"]
        assert isinstance(file1, UploadFile)
        assert file1.filename == "test.txt"
        assert file1.content_type == "text/plain"
        content1 = await file1.read()
        assert content1 == b"Hello, World!"
        
        # Проверяем второй файл
        file2 = files["file2"]
        assert isinstance(file2, UploadFile)
        assert file2.filename == "image.jpg"
        assert file2.content_type == "image/jpeg"
        content2 = await file2.read()
        assert content2 == b"binary data"
        
    @pytest.mark.asyncio
    async def test_file_save(self):
        # Создаем временную директорию для теста
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем файл
            file = UploadFile("test.txt")
            await file.write(b"Hello, World!")
            
            # Сохраняем файл
            path = os.path.join(temp_dir, "test.txt")
            await file.save(path)
            
            # Проверяем, что файл существует и содержит правильные данные
            assert os.path.exists(path)
            with open(path, "rb") as f:
                content = f.read()
                assert content == b"Hello, World!"
                
    @pytest.mark.asyncio
    async def test_file_context_manager(self):
        # Создаем файл
        file = UploadFile("test.txt")
        await file.write(b"Hello, World!")
        
        # Используем контекстный менеджер
        async with file as f:
            content = await f.read()
            assert content == b"Hello, World!"
            
        # Проверяем, что файл закрыт
        with pytest.raises(ValueError):
            await file.read()
            
    @pytest.mark.asyncio
    async def test_file_iterator(self):
        # Создаем файл с разумным размером содержимого
        data = b"Hello, " * 100 + b"World!"  # ~700 байт
        file = UploadFile("test.txt")
        await file.write(data)
        
        # Сбрасываем позицию файла в начало перед чтением
        await file.seek(0)
        
        # Читаем файл по частям
        chunks = []
        async for chunk in file:
            chunks.append(chunk)
            
        # Проверяем, что все данные прочитаны
        assert b"".join(chunks) == data
        
        # Закрываем файл после использования
        await file.close()

class TestResponse:
    @pytest.mark.asyncio
    async def test_response_json(self):
        response = Response.json({"hello": "world"})
        assert response.status_code == 200
        assert await response.body == b'{"hello": "world"}'
        assert (b"content-type", b"application/json") in response.headers_list
        
    @pytest.mark.asyncio
    async def test_response_text(self):
        response = Response.text("Hello, World!")
        assert response.status_code == 200
        assert await response.body == b"Hello, World!"
        assert (b"content-type", b"text/plain") in response.headers_list
        
    @pytest.mark.asyncio
    async def test_response_html(self):
        response = Response.html("<h1>Hello, World!</h1>")
        assert response.status_code == 200
        assert await response.body == b"<h1>Hello, World!</h1>"
        assert (b"content-type", b"text/html") in response.headers_list
        
    def test_response_redirect(self):
        response = Response.redirect("/new-url")
        assert response.status_code == 302
        assert response.headers["location"] == "/new-url"
        
    def test_response_cookies(self):
        response = Response.text("Hello, World!")
        response.set_cookie(
            "session",
            "abc123",
            max_age=3600,
            path="/",
            secure=True,
            httponly=True,
            samesite="lax"
        )
        
        cookie_headers = [h for h in response.headers_list if h[0] == b"set-cookie"]
        assert len(cookie_headers) == 1
        cookie_value = cookie_headers[0][1].decode()
        assert "session=abc123" in cookie_value
        assert "Max-Age=3600" in cookie_value
        assert "Path=/" in cookie_value
        assert "Secure" in cookie_value
        assert "HttpOnly" in cookie_value
        assert "SameSite=lax" in cookie_value
        
    def test_response_delete_cookie(self):
        response = Response.text("Hello, World!")
        response.delete_cookie("session")
        
        cookie_headers = [h for h in response.headers_list if h[0] == b"set-cookie"]
        assert len(cookie_headers) == 1
        cookie_value = cookie_headers[0][1].decode()
        assert "session=" in cookie_value
        assert "Max-Age=0" in cookie_value

    @pytest.mark.asyncio
    async def test_response_stream(self):
        # Создаем асинхронный генератор для тестовых данных
        async def stream_data():
            for i in range(3):
                yield f"chunk {i}".encode()
                
        # Создаем потоковый ответ
        response = Response.stream(stream_data())
        assert response.is_stream
        assert (b"transfer-encoding", b"chunked") in response.headers_list
        
        # Проверяем, что нельзя получить тело потокового ответа
        with pytest.raises(RuntimeError):
            await response.body
            
        # Проверяем отправку ответа
        messages = []
        async def send(message):
            messages.append(message)
            
        await response(send)
        
        # Проверяем сообщения
        assert len(messages) == 5  # start + 3 chunks + end
        assert messages[0]["type"] == "http.response.start"
        assert messages[0]["status"] == 200
        
        assert messages[1]["type"] == "http.response.body"
        assert messages[1]["body"] == b"chunk 0"
        assert messages[1]["more_body"] is True
        
        assert messages[2]["type"] == "http.response.body"
        assert messages[2]["body"] == b"chunk 1"
        assert messages[2]["more_body"] is True
        
        assert messages[3]["type"] == "http.response.body"
        assert messages[3]["body"] == b"chunk 2"
        assert messages[3]["more_body"] is True
        
        assert messages[4]["type"] == "http.response.body"
        assert messages[4]["body"] == b""
        assert messages[4]["more_body"] is False
        
    @pytest.mark.asyncio
    async def test_response_stream_with_media_type(self):
        async def stream_data():
            yield b"<data>"
            
        # Создаем потоковый ответ с указанием media_type
        response = Response.stream(
            stream_data(),
            media_type="application/xml"
        )
        
        assert (b"content-type", b"application/xml") in response.headers_list
        
    @pytest.mark.asyncio
    async def test_response_stream_with_custom_headers(self):
        async def stream_data():
            yield b"data"
            
        # Создаем потоковый ответ с пользовательскими заголовками
        response = Response.stream(
            stream_data(),
            headers={"x-custom": "value"}
        )
        
        assert (b"x-custom", b"value") in response.headers_list 