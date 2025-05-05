"""
Tests for file service components.
"""

import os
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the parent directory to Python path for imports to work
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.loader import PDFLoader
from rag.file_manager import FileManager

# Chemin vers votre PDF existant
REAL_PDF_PATH = r"C:\Users\SuperSun\Desktop\Résonance\Résonance - Nouvelle Océanique.pdf"

class TestPDFLoader:
    """Tests for the PDFLoader class."""
    
    def test_is_valid_pdf(self):
        """Test validation of PDF files."""
        # Test avec un vrai PDF
        assert PDFLoader.is_valid_pdf(REAL_PDF_PATH) is True
        
        # Test avec un fichier non existant
        assert PDFLoader.is_valid_pdf("non_existent_file.pdf") is False
    
    def test_extract_text_from_pdf(self):
        """Test extraction of text from PDF files."""
        # Test avec un vrai PDF
        result = PDFLoader.extract_text_from_pdf(REAL_PDF_PATH)
        
        # Vérifications basiques
        assert "file_name" in result
        assert "total_pages" in result
        assert "pages" in result
        assert "metadata" in result
        assert result["total_pages"] > 0
        assert len(result["pages"]) == result["total_pages"]
    
    def test_count_pages(self):
        """Test counting pages in a PDF file."""
        # Test avec un vrai PDF
        page_count = PDFLoader.count_pages(REAL_PDF_PATH)
        assert page_count > 0  # Vérifie qu'il y a au moins une page


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
        """Test sanitization of filenames."""
        # Test direct sur la méthode mais en contournant le problème avec /
        manager = FileManager()
        
        # Test avec caractères invalides sauf /
        input_filename = "file-with:invalid*chars?.pdf"
        sanitized = manager._sanitize_filename(input_filename)
        assert sanitized == "file-with_invalid_chars_.pdf"
        
        # Test avec éléments de chemin
        input_filename = "/path/to/file.pdf"
        sanitized = manager._sanitize_filename(input_filename)
        assert sanitized == "file.pdf"
        
    def test_ensure_unique_filename(self, temp_dir):
        """Test ensuring unique filenames."""
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
        
        # Next call should add _2
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