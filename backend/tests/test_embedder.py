# backend/tests/test_embedder.py
"""
Tests for the RAG embedder module.
"""

import os
import sys
import pytest
import numpy as np
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.embedder import Embedder, EmbeddingCache
from rag.chunker import Chunk


class TestEmbeddingCache:
    """Tests for the EmbeddingCache class."""
    
    def setup_method(self):
        """Setup for tests."""
        self.cache_dir = "test_cache"
        self.cache = EmbeddingCache(cache_dir=self.cache_dir)
    
    def teardown_method(self):
        """Cleanup after tests."""
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
    
    def test_cache_key_generation(self):
        """Test generating cache keys."""
        text = "This is a test"
        model_name = "test-model"
        
        key = self.cache._get_cache_key(text, model_name)
        
        assert isinstance(key, str)
        assert len(key) > 0
    
    def test_cache_miss(self):
        """Test cache miss."""
        text = "This is a test"
        model_name = "test-model"
        
        result = self.cache.get(text, model_name)
        
        assert result is None
    
    def test_cache_hit(self):
        """Test cache hit."""
        text = "This is a test"
        model_name = "test-model"
        embedding = np.array([0.1, 0.2, 0.3])
        
        self.cache.set(text, model_name, embedding)
        result = self.cache.get(text, model_name)
        
        assert result is not None
        assert np.array_equal(result, embedding)
    
    def test_clear_cache(self):
        """Test clearing the cache."""
        text = "This is a test"
        model_name = "test-model"
        embedding = np.array([0.1, 0.2, 0.3])
        
        self.cache.set(text, model_name, embedding)
        
        # Clear with max age 0 to clear everything
        removed = self.cache.clear(max_age_days=0)
        
        assert removed > 0
        assert self.cache.get(text, model_name) is None


class TestEmbedder:
    """Tests for the Embedder class."""
    
    @patch('rag.embedder.SentenceTransformer')
    def test_embedder_initialization(self, mock_transformer):
        """Test embedder initialization."""
        # Mock the SentenceTransformer class
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model
        
        embedder = Embedder(model_name="test-model", cache_enabled=False)
        embedder.load_model()
        
        assert embedder.model is not None
        assert embedder.model_name == "test-model"
        assert embedder.dimension == 384
    
    @patch('rag.embedder.SentenceTransformer')
    def test_embed_text(self, mock_transformer):
        """Test embedding a single text."""
        # Mock the SentenceTransformer class
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_transformer.return_value = mock_model
        
        embedder = Embedder(model_name="test-model", cache_enabled=False)
        embedder.load_model()
        
        embedding = embedder.embed_text("This is a test")
        
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == 3
        mock_model.encode.assert_called_once()
    
    @patch('rag.embedder.SentenceTransformer')
    def test_embed_texts(self, mock_transformer):
        """Test embedding multiple texts."""
        # Mock the SentenceTransformer class
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        mock_transformer.return_value = mock_model
        
        embedder = Embedder(model_name="test-model", cache_enabled=False)
        embedder.load_model()
        
        embeddings = embedder.embed_texts(["Text 1", "Text 2"])
        
        assert len(embeddings) == 2
        assert all(isinstance(emb, np.ndarray) for emb in embeddings)
        mock_model.encode.assert_called_once()
    
    @patch('rag.embedder.SentenceTransformer')
    def test_embed_chunks(self, mock_transformer):
        """Test embedding chunks."""
        # Mock the SentenceTransformer class
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        mock_transformer.return_value = mock_model
        
        embedder = Embedder(model_name="test-model", cache_enabled=False)
        embedder.load_model()
        
        chunks = [
            Chunk(text="Text 1", index=0, source_id=1, source_type="test"),
            Chunk(text="Text 2", index=1, source_id=1, source_type="test")
        ]
        
        chunk_embeddings = embedder.embed_chunks(chunks)
        
        assert len(chunk_embeddings) == 2
        assert all(isinstance(chunk, Chunk) for chunk, _ in chunk_embeddings)
        assert all(isinstance(emb, np.ndarray) for _, emb in chunk_embeddings)
        mock_model.encode.assert_called_once()
    
    @patch('rag.embedder.SentenceTransformer')
    def test_with_cache(self, mock_transformer):
        """Test using the embedder with cache."""
        # Mock the SentenceTransformer class
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_transformer.return_value = mock_model
        
        # Create a temporary cache directory
        cache_dir = "test_embedder_cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        try:
            embedder = Embedder(model_name="test-model", cache_enabled=True)
            embedder.cache = EmbeddingCache(cache_dir=cache_dir)
            embedder.load_model()
            
            # First call should miss cache
            embedding1 = embedder.embed_text("This is a test")
            
            # Second call should hit cache
            embedding2 = embedder.embed_text("This is a test")
            
            assert np.array_equal(embedding1, embedding2)
            mock_model.encode.assert_called_once()  # Should only be called once
            
        finally:
            # Clean up
            import shutil
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)