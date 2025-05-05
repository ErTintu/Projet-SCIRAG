"""
Tests for file service components.
"""

import os
import pytest
import tempfile
from pathlib import Path
import shutil
from unittest.mock import patch, MagicMock

# Add the parent directory to Python path for imports to work
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.loader import PDFLoader
from rag.file_manager import FileManager


def create_minimal_pdf(filepath):
    """Create a minimal valid PDF file for testing."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(b'%PDF-1.4\n%EOF\n')
    return filepath


class TestPDFLoader:
    """Tests for the PDFLoader class."""
    
    @pytest.fixture(scope="class")
    def sample_pdf_path(self):
        """Create a temporary sample PDF file for testing."""
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        # Create a minimal PDF file
        pdf_path = os.path.join(temp_dir, "sample.pdf")
        create_minimal_pdf(pdf_path)
        
        yield pdf_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_is_valid_pdf(self, sample_pdf_path):
        """Test PDF validation."""
        # Test with real minimal PDF
        assert PDFLoader.is_valid_pdf(sample_pdf_path) is True
        
        # Test with non-existent file
        assert PDFLoader.is_valid_pdf("non_existent.pdf") is False
        
        # Test with non-PDF file
        non_pdf_path = os.path.join(os.path.dirname(sample_pdf_path), "not_a_pdf.txt")
        with open(non_pdf_path, 'w') as f:
            f.write("This is not a PDF")
        assert PDFLoader.is_valid_pdf(non_pdf_path) is False
    
    def test_extract_text_from_pdf(self, sample_pdf_path):
        """Test text extraction from PDF."""
        # Use patch to mock PdfReader behavior
        with patch('pypdf.PdfReader') as mock_reader_class:
            # Set up mock reader
            mock_reader = MagicMock()
            mock_reader_class.return_value = mock_reader
            
            # Mock pages
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Test content"
            mock_reader.pages = [mock_page]
            
            # Mock metadata
            mock_reader.metadata = MagicMock(
                title="Test PDF",
                author="Test Author",
                subject=None,
                creator=None,
                producer=None,
                creation_date=None
            )
            
            # Call the function
            result = PDFLoader.extract_text_from_pdf(sample_pdf_path)
            
            # Check results
            assert result["file_name"] == os.path.basename(sample_pdf_path)
            assert result["total_pages"] == 1
            assert len(result["pages"]) == 1
            assert result["pages"][0]["content"] == "Test content"
            assert result["metadata"]["title"] == "Test PDF"
            assert result["metadata"]["author"] == "Test Author"
    
    def test_count_pages(self, sample_pdf_path):
        """Test page counting."""
        with patch('pypdf.PdfReader') as mock_reader_class:
            mock_reader = MagicMock()
            mock_reader.pages = [MagicMock(), MagicMock(), MagicMock()]  # 3 pages
            mock_reader_class.return_value = mock_reader
            
            assert PDFLoader.count_pages(sample_pdf_path) == 3


class TestFileManager:
    """Tests for the FileManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_get_corpus_dir(self, temp_dir):
        """Test getting corpus directory."""
        manager = FileManager(base_upload_dir=temp_dir)
        corpus_dir = manager.get_corpus_dir(123)
        
        # Check path structure
        expected_path = os.path.join(temp_dir, "rag", "123")
        assert corpus_dir == expected_path
        
        # Check directory was created
        assert os.path.exists(corpus_dir)
        assert os.path.isdir(corpus_dir)
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Create a modified FileManager to test just the sanitize function
        class TestFileManager(FileManager):
            def test_sanitize(self, filename):
                return self._sanitize_filename(filename)
        
        manager = TestFileManager()
        
        # Test replacing invalid characters
        assert manager.test_sanitize("file/with:invalid*chars?.pdf") == "file_with_invalid_chars_.pdf"
        
        # Test path stripping
        assert manager.test_sanitize("/path/to/file.pdf") == "file.pdf"
    
    def test_ensure_unique_filename(self, temp_dir):
        """Test filename uniqueness handling."""
        # Create a test file
        test_file = os.path.join(temp_dir, "test.pdf")
        with open(test_file, "w") as f:
            f.write("test")
        
        manager = FileManager()
        
        # First call should add _1 since file exists
        unique_name = manager._ensure_unique_filename(test_file)
        assert unique_name == os.path.join(temp_dir, "test_1.pdf")
        
        # Create the _1 file as well
        with open(unique_name, "w") as f:
            f.write("test")
        
        # Now should return _2
        unique_name = manager._ensure_unique_filename(test_file)
        assert unique_name == os.path.join(temp_dir, "test_2.pdf")
    
    def test_delete_file(self, temp_dir):
        """Test file deletion."""
        # Create a test file
        test_file = os.path.join(temp_dir, "test.pdf")
        with open(test_file, "w") as f:
            f.write("test")
        
        manager = FileManager()
        
        # Test deletion success
        assert manager.delete_file(test_file) is True
        assert not os.path.exists(test_file)
        
        # Test deletion failure (file already gone)
        assert manager.delete_file(test_file) is False