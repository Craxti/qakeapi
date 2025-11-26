"""
Tests for file upload functionality.
"""

from pathlib import Path
import pytest
from qakeapi.core.files import (
    FileUpload,
    MultipartParser,
    parse_multipart,
    IMAGE_TYPES,
    DOCUMENT_TYPES,
)


class TestFileUpload:
    """Tests for FileUpload class."""
    
    def test_file_upload_creation(self):
        """Test creating FileUpload."""
        content = b"test file content"
        file = FileUpload(
            filename="test.txt",
            content=content,
            content_type="text/plain"
        )
        
        assert file.filename == "test.txt"
        assert file.content == content
        assert file.content_type == "text/plain"
        assert file.size == len(content)
    
    def test_file_upload_properties(self):
        """Test FileUpload properties."""
        file = FileUpload(
            filename="image.jpg",
            content=b"image data",
            content_type="image/jpeg"
        )
        
        assert file.extension == "jpg"
        assert file.name == "image"
        assert file.size == 10
    
    def test_file_upload_read(self):
        """Test reading file content."""
        content = b"test content"
        file = FileUpload(filename="test.txt", content=content)
        
        assert file.read() == content
        assert file.read_text() == "test content"
    
    def test_file_upload_validate_size(self):
        """Test file size validation."""
        file = FileUpload(filename="test.txt", content=b"x" * 100)
        
        assert file.validate_size(200) is True
        assert file.validate_size(50) is False
    
    def test_file_upload_validate_type(self):
        """Test file type validation."""
        file = FileUpload(filename="image.jpg", content=b"data")
        
        assert file.validate_type({"jpg", "png"}) is True
        assert file.validate_type({"pdf", "doc"}) is False
    
    def test_file_upload_validate_content_type(self):
        """Test content type validation."""
        file = FileUpload(
            filename="image.jpg",
            content=b"data",
            content_type="image/jpeg"
        )
        
        assert file.validate_content_type({"image/jpeg", "image/png"}) is True
        assert file.validate_content_type({"application/pdf"}) is False


class TestMultipartParser:
    """Tests for MultipartParser."""
    
    def test_parse_simple_multipart(self):
        """Test parsing simple multipart form."""
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        parser = MultipartParser(boundary)
        
        body = (
            b'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            b'Content-Disposition: form-data; name="field1"\r\n\r\n'
            b'value1\r\n'
            b'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            b'Content-Disposition: form-data; name="field2"\r\n\r\n'
            b'value2\r\n'
            b'------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'
        )
        
        result = parser.parse(body)
        
        assert "fields" in result
        assert "files" in result
        assert result["fields"]["field1"] == "value1"
        assert result["fields"]["field2"] == "value2"
    
    def test_parse_multipart_with_file(self):
        """Test parsing multipart with file upload."""
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        parser = MultipartParser(boundary)
        
        body = (
            b'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            b'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
            b'Content-Type: text/plain\r\n\r\n'
            b'file content here\r\n'
            b'------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'
        )
        
        result = parser.parse(body)
        
        assert "files" in result
        assert "file" in result["files"]
        file = result["files"]["file"]
        assert isinstance(file, FileUpload)
        assert file.filename == "test.txt"
        assert file.content == b"file content here"
        assert file.content_type == "text/plain"


class TestParseMultipart:
    """Tests for parse_multipart function."""
    
    def test_parse_multipart_function(self):
        """Test parse_multipart function."""
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        content_type = f'multipart/form-data; boundary={boundary}'
        
        body = (
            b'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
            b'Content-Disposition: form-data; name="field1"\r\n\r\n'
            b'value1\r\n'
            b'------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'
        )
        
        result = parse_multipart(body, content_type)
        
        assert "fields" in result
        assert result["fields"]["field1"] == "value1"
    
    def test_parse_multipart_invalid_content_type(self):
        """Test parse_multipart with invalid content type."""
        with pytest.raises(ValueError, match="Content-Type must be multipart/form-data"):
            parse_multipart(b"", "application/json")
    
    def test_parse_multipart_missing_boundary(self):
        """Test parse_multipart with missing boundary."""
        with pytest.raises(ValueError, match="Missing boundary"):
            parse_multipart(b"", "multipart/form-data")


class TestFileUploadIntegration:
    """Integration tests for file upload."""
    
    @pytest.mark.asyncio
    async def test_file_upload_save(self, tmp_path):
        """Test saving uploaded file."""
        file = FileUpload(
            filename="test.txt",
            content=b"test content"
        )
        
        saved_path = await file.save(str(tmp_path))
        
        assert (tmp_path / "test.txt").exists()
        assert (tmp_path / "test.txt").read_bytes() == b"test content"
        assert saved_path == str((tmp_path / "test.txt").absolute())
    
    @pytest.mark.asyncio
    async def test_file_upload_save_custom_filename(self, tmp_path):
        """Test saving with custom filename."""
        file = FileUpload(
            filename="original.txt",
            content=b"content"
        )
        
        saved_path = await file.save(str(tmp_path), filename="custom.txt")
        
        assert (tmp_path / "custom.txt").exists()
        assert saved_path == str((tmp_path / "custom.txt").absolute())
    
    def test_file_upload_save_to_temp(self):
        """Test saving to temporary file."""
        file = FileUpload(
            filename="test.txt",
            content=b"temp content"
        )
        
        temp_path = file.save_to_temp()
        
        try:
            assert Path(temp_path).exists()
            assert Path(temp_path).read_bytes() == b"temp content"
        finally:
            Path(temp_path).unlink()

