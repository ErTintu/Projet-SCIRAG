"""
PDF loading and text extraction service for SCIRAG.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import tempfile

import pypdf
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PDFLoader:
    """Service for loading and extracting text from PDF documents."""

    @staticmethod
    def extract_text_from_pdf(file_path: str, extract_metadata: bool = True) -> Dict[str, Any]:
        """
        Extract text and metadata from a PDF file.

        Args:
            file_path: Path to the PDF file
            extract_metadata: Whether to extract metadata

        Returns:
            Dictionary containing extracted text and metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            reader = PdfReader(file_path)
            
            # Extract text from each page
            pages = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    pages.append({
                        "page_number": i + 1,
                        "content": page_text.strip(),
                        "char_count": len(page_text)
                    })
            
            # Get document metadata
            metadata = {}
            if extract_metadata and reader.metadata:
                meta = reader.metadata
                metadata = {
                    "title": meta.title if meta.title else None,
                    "author": meta.author if meta.author else None,
                    "subject": meta.subject if meta.subject else None,
                    "creator": meta.creator if meta.creator else None,
                    "producer": meta.producer if meta.producer else None,
                    "creation_date": meta.creation_date.strftime("%Y-%m-%d %H:%M:%S") if meta.creation_date else None,
                }
            
            # Build result
            result = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "total_pages": len(reader.pages),
                "metadata": metadata,
                "pages": pages,
                "full_text": "\n\n".join([page["content"] for page in pages])
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise

    @staticmethod
    def extract_text_from_binary(file_content: bytes, file_name: str = "temp.pdf") -> Dict[str, Any]:
        """
        Extract text from binary PDF content.

        Args:
            file_content: Binary content of the PDF file
            file_name: Name to use for the temporary file

        Returns:
            Dictionary containing extracted text and metadata
        """
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_path = temp_file.name
            temp_file.write(file_content)
        
        try:
            # Extract text using the file path function
            result = PDFLoader.extract_text_from_pdf(temp_path)
            
            # Update file name in the result
            result["file_name"] = file_name
            
            return result
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @staticmethod
    def extract_text_by_pages(file_path: str) -> List[str]:
        """
        Extract text from PDF document page by page.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of strings, one per page
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            reader = PdfReader(file_path)
            return [page.extract_text() for page in reader.pages]
        except Exception as e:
            logger.error(f"Error extracting text by pages from PDF {file_path}: {e}")
            raise

    @staticmethod
    def is_valid_pdf(file_path: str) -> bool:
        """
        Check if a file is a valid PDF.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file is a valid PDF, False otherwise
        """
        if not os.path.exists(file_path):
            return False
            
        try:
            # Try to open the file as PDF
            with open(file_path, 'rb') as f:
                # Check if the file starts with the PDF signature
                if not f.read(4) == b'%PDF':
                    return False
                
            # Try to read with PyPDF
            reader = PdfReader(file_path)
            if len(reader.pages) > 0:
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def count_pages(file_path: str) -> int:
        """
        Count the number of pages in a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Number of pages
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            reader = PdfReader(file_path)
            return len(reader.pages)
        except Exception as e:
            logger.error(f"Error counting pages in PDF {file_path}: {e}")
            raise

    @staticmethod
    def get_pdf_metadata(file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing PDF metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            reader = PdfReader(file_path)
            if not reader.metadata:
                return {}
                
            meta = reader.metadata
            metadata = {
                "title": meta.title if meta.title else None,
                "author": meta.author if meta.author else None,
                "subject": meta.subject if meta.subject else None,
                "creator": meta.creator if meta.creator else None,
                "producer": meta.producer if meta.producer else None,
                "creation_date": meta.creation_date.strftime("%Y-%m-%d %H:%M:%S") if meta.creation_date else None,
            }
            
            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata from PDF {file_path}: {e}")
            raise