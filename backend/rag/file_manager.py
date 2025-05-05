"""
File management utilities for SCIRAG.
"""

import os
import shutil
import logging
import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import UploadFile

logger = logging.getLogger(__name__)


class FileManager:
    """Manager for handling file uploads and storage."""

    def __init__(self, base_upload_dir: str = "uploads"):
        """
        Initialize the file manager.

        Args:
            base_upload_dir: Base directory for file uploads
        """
        self.base_upload_dir = base_upload_dir
        os.makedirs(self.base_upload_dir, exist_ok=True)

    def get_corpus_dir(self, corpus_id: int) -> str:
        """
        Get the upload directory for a specific corpus.

        Args:
            corpus_id: ID of the RAG corpus

        Returns:
            Path to the corpus directory
        """
        corpus_dir = os.path.join(self.base_upload_dir, "rag", str(corpus_id))
        os.makedirs(corpus_dir, exist_ok=True)
        return corpus_dir

    async def save_upload_file(self, file: UploadFile, corpus_id: int) -> Dict[str, Any]:
        """
        Save an uploaded file to the appropriate directory.

        Args:
            file: UploadFile object from FastAPI
            corpus_id: ID of the RAG corpus

        Returns:
            Dictionary with file info
        """
        if not file.filename:
            raise ValueError("File has no filename")

        # Get corpus directory
        corpus_dir = self.get_corpus_dir(corpus_id)
        
        # Sanitize filename and ensure uniqueness
        filename = self._sanitize_filename(file.filename)
        file_path = os.path.join(corpus_dir, filename)
        
        # Make sure the file doesn't already exist
        file_path = self._ensure_unique_filename(file_path)
        
        # Save file content
        with open(file_path, "wb") as f:
            file_content = await file.read()
            f.write(file_content)
        
        # Get file info
        file_info = {
            "corpus_id": corpus_id,
            "filename": os.path.basename(file_path),
            "file_path": file_path,
            "file_type": self._get_file_extension(file_path),
            "file_size": os.path.getsize(file_path)
        }
        
        return file_info

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from the filesystem.

        Args:
            file_path: Path to the file to delete

        Returns:
            True if file was deleted, False otherwise
        """
        if not os.path.exists(file_path):
            logger.warning(f"Cannot delete file {file_path}: file not found")
            return False
            
        try:
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False

    def delete_corpus_files(self, corpus_id: int) -> bool:
        """
        Delete all files for a corpus.

        Args:
            corpus_id: ID of the RAG corpus

        Returns:
            True if directory was deleted, False otherwise
        """
        corpus_dir = os.path.join(self.base_upload_dir, "rag", str(corpus_id))
        if not os.path.exists(corpus_dir):
            logger.warning(f"Cannot delete corpus directory {corpus_dir}: directory not found")
            return False
            
        try:
            shutil.rmtree(corpus_dir)
            logger.info(f"Deleted corpus directory: {corpus_dir}")
            return True
        except Exception as e:
            logger.error(f"Error deleting corpus directory {corpus_dir}: {e}")
            return False

    def list_corpus_files(self, corpus_id: int) -> List[Dict[str, Any]]:
        """
        List all files in a corpus directory.

        Args:
            corpus_id: ID of the RAG corpus

        Returns:
            List of dictionaries with file info
        """
        corpus_dir = os.path.join(self.base_upload_dir, "rag", str(corpus_id))
        if not os.path.exists(corpus_dir):
            logger.warning(f"Corpus directory {corpus_dir} not found")
            return []
            
        files = []
        for filename in os.listdir(corpus_dir):
            file_path = os.path.join(corpus_dir, filename)
            if os.path.isfile(file_path):
                files.append({
                    "filename": filename,
                    "file_path": file_path,
                    "file_type": self._get_file_extension(file_path),
                    "file_size": os.path.getsize(file_path)
                })
                
        return files

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to ensure it is safe to use.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        import re
        # Keep only filename, not path
        filename = os.path.basename(filename)
        
        # Replace problematic characters using regex
        filename = re.sub(r'[/\\:*?"<>|]', '_', filename)
        
        return filename

    def _ensure_unique_filename(self, file_path: str) -> str:
        """
        Ensure a filename is unique by adding a counter if necessary.

        Args:
            file_path: Desired file path

        Returns:
            Unique file path
        """
        if not os.path.exists(file_path):
            return file_path
            
        # Split into base name and extension
        base, ext = os.path.splitext(file_path)
        counter = 1
        
        # Keep trying with incremented counter until we find a unique name
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
            
        return f"{base}_{counter}{ext}"

    def _get_file_extension(self, file_path: str) -> str:
        """
        Get file extension from a path.

        Args:
            file_path: Path to the file

        Returns:
            File extension (lowercase, without the dot)
        """
        _, ext = os.path.splitext(file_path)
        return ext.lower().lstrip('.')