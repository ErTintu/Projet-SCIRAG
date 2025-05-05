# backend/tests/test_store.py
"""
Tests for the RAG vector store module.
"""

import os
import sys
import pytest
import numpy as np
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.store import SearchResult, ChromaStore
from rag.chunker import Chunk


class TestSearchResult:
    """Tests for the SearchResult class."""
    
    def test_search_result_creation(self):
        """Test creating a search result."""
        chunk = Chunk(text="This is a test", index=0, source_id=1, source_type="document")
        score = 0.95
        
        result = SearchResult(chunk=chunk, score=score)
        
        assert result.chunk == chunk
        assert result.score == score
        assert result.metadata == {}
    
    def test_search_result_with_metadata(self):
        """Test creating a search result with metadata."""
        chunk = Chunk(text="This is a test", index=0, source_id=1, source_type="document")
        score = 0.95
        metadata = {"key": "value"}
        
        result = SearchResult(chunk=chunk, score=score, metadata=metadata)
        
        assert result.metadata == metadata
    
    def test_search_result_to_dict(self):
        """Test converting a search result to a dictionary."""
        chunk = Chunk(text="This is a test", index=0, source_id=1, source_type="document")
        score = 0.95
        metadata = {"key": "value"}
        
        result = SearchResult(chunk=chunk, score=score, metadata=metadata)
        result_dict = result.to_dict()
        
        assert result_dict["chunk"] == chunk.to_dict()
        assert result_dict["score"] == score
        assert result_dict["metadata"] == metadata
    
    def test_search_result_from_dict(self):
        """Test creating a search result from a dictionary."""
        chunk_dict = {
            "text": "This is a test",
            "index": 0,
            "source_id": 1,
            "source_type": "document",
            "metadata": {}
        }
        
        result_dict = {
            "chunk": chunk_dict,
            "score": 0.95,
            "metadata": {"key": "value"}
        }
        
        result = SearchResult.from_dict(result_dict)
        
        assert result.chunk.text == "This is a test"
        assert result.score == 0.95
        assert result.metadata == {"key": "value"}
    
    def test_search_result_str(self):
        """Test the string representation of a search result."""
        chunk = Chunk(text="This is a test", index=0, source_id=1, source_type="document")
        score = 0.95
        
        result = SearchResult(chunk=chunk, score=score)
        
        assert "0.9500" in str(result)
        assert str(chunk) in str(result)


@pytest.mark.skipif(not os.environ.get("RUN_CHROMA_TESTS"), reason="Skipping ChromaDB tests")
class TestChromaStore:
    """Tests for the ChromaStore class."""
    
    def setup_method(self):
        """Setup for tests."""
        self.test_dir = "test_chroma_data"
        self.collection_name = "test_collection"
        
        # Create a ChromaStore instance for testing
        self.store = ChromaStore(
            persist_directory=self.test_dir,
            collection_name=self.collection_name
        )
        
        # Reset the collection to ensure a clean state
        self.store.reset()
    
    def teardown_method(self):
        """Cleanup after tests."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_add_chunks(self):
        """Test adding chunks to the store."""
        chunks = [
            Chunk(text="This is document 1", index=0, source_id=1, source_type="document"),
            Chunk(text="This is document 2", index=1, source_id=2, source_type="document")
        ]
        
        embeddings = [
            np.array([0.1, 0.2, 0.3]),
            np.array([0.4, 0.5, 0.6])
        ]
        
        self.store.add_chunks(chunks, embeddings)
        
        # Check that chunks were added
        assert self.store.get_chunk_count() == 2
    
    def test_search(self):
        """Test searching for chunks."""
        # First add some chunks
        chunks = [
            Chunk(text="This is about machine learning", index=0, source_id=1, source_type="document"),
            Chunk(text="This is about data science", index=1, source_id=2, source_type="document"),
            Chunk(text="This is about cooking recipes", index=2, source_id=3, source_type="document")
        ]
        
        embeddings = [
            np.array([0.1, 0.2, 0.3]),
            np.array([0.15, 0.25, 0.35]),
            np.array([0.9, 0.8, 0.7])
        ]
        
        self.store.add_chunks(chunks, embeddings)
        
        # Search for something similar to the first two chunks
        query_embedding = np.array([0.2, 0.3, 0.4])
        results = self.store.search(query_embedding, limit=2)
        
        assert len(results) == 2
        # The first two chunks should be more similar to the query than the third
        result_ids = {f"{result.chunk.source_type}_{result.chunk.source_id}" for result in results}
        assert "document_1" in result_ids or "document_2" in result_ids
    
    def test_delete_chunks(self):
        """Test deleting chunks from the store."""
        # First add some chunks
        chunks = [
            Chunk(text="Chunk 1", index=0, source_id=1, source_type="document"),
            Chunk(text="Chunk 2", index=1, source_id=1, source_type="document")
        ]
        
        embeddings = [
            np.array([0.1, 0.2, 0.3]),
            np.array([0.4, 0.5, 0.6])
        ]
        
        self.store.add_chunks(chunks, embeddings)
        assert self.store.get_chunk_count() == 2
        
        # Delete one chunk
        self.store.delete_chunks(["document_1_0"])
        assert self.store.get_chunk_count() == 1
    
    def test_delete_by_source(self):
        """Test deleting chunks by source."""
        # First add some chunks from different sources
        chunks = [
            Chunk(text="Document 1 Chunk 1", index=0, source_id=1, source_type="document"),
            Chunk(text="Document 1 Chunk 2", index=1, source_id=1, source_type="document"),
            Chunk(text="Document 2 Chunk 1", index=0, source_id=2, source_type="document")
        ]
        
        embeddings = [
            np.array([0.1, 0.2, 0.3]),
            np.array([0.4, 0.5, 0.6]),
            np.array([0.7, 0.8, 0.9])
        ]
        
        self.store.add_chunks(chunks, embeddings)
        assert self.store.get_chunk_count() == 3
        
        # Delete all chunks from source 1
        self.store.delete_by_source("document", 1)
        assert self.store.get_chunk_count() == 1
    
    def test_get_instance(self):
        """Test getting a singleton instance."""
        store1 = ChromaStore.get_instance(
            persist_directory=self.test_dir,
            collection_name=self.collection_name
        )
        
        store2 = ChromaStore.get_instance(
            persist_directory=self.test_dir,
            collection_name=self.collection_name
        )
        
        # Should be the same instance
        assert store1 is store2
        
        # A different collection name should give a different instance
        store3 = ChromaStore.get_instance(
            persist_directory=self.test_dir,
            collection_name="different_collection"
        )
                
        # Should be a different instance
        assert store1 is not store3