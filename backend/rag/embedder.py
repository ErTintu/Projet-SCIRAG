"""
Embedding service for RAG system.

This module provides functionality to convert text chunks into vector embeddings
using sentence-transformers models.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
from pathlib import Path
import pickle
import hashlib
import time
from functools import lru_cache

# Import sentence-transformers
from sentence_transformers import SentenceTransformer

from .chunker import Chunk

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """Cache for text embeddings to avoid recomputing."""
    
    def __init__(self, cache_dir: str = "cache/embeddings", max_age_days: int = 30):
        """
        Initialize the embedding cache.
        
        Args:
            cache_dir: Directory to store cached embeddings
            max_age_days: Maximum age in days for cached embeddings
        """
        self.cache_dir = cache_dir
        self.max_age_seconds = max_age_days * 24 * 60 * 60
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_key(self, text: str, model_name: str) -> str:
        """
        Generate a unique cache key for a text and model.
        
        Args:
            text: Text to be embedded
            model_name: Name of the embedding model
            
        Returns:
            Cache key string
        """
        # Hash the text and model name to create a unique key
        text_hash = hashlib.md5(text.encode()).hexdigest()
        model_hash = hashlib.md5(model_name.encode()).hexdigest()
        return f"{model_hash[:8]}_{text_hash[:16]}"
    
    def _get_cache_file_path(self, key: str) -> str:
        """
        Get file path for a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            File path
        """
        return os.path.join(self.cache_dir, f"{key}.pkl")
    
    def get(self, text: str, model_name: str) -> Optional[np.ndarray]:
        """
        Get embedding from cache if available.
        
        Args:
            text: Text to get embedding for
            model_name: Name of the embedding model
            
        Returns:
            Numpy array with embedding or None if not in cache
        """
        key = self._get_cache_key(text, model_name)
        file_path = self._get_cache_file_path(key)
        
        if not os.path.exists(file_path):
            return None
        
        # Check if cache is expired
        file_age = time.time() - os.path.getmtime(file_path)
        if file_age > self.max_age_seconds:
            logger.debug(f"Cache expired for key {key}")
            return None
        
        try:
            with open(file_path, "rb") as f:
                cache_data = pickle.load(f)
                return cache_data["embedding"]
        except Exception as e:
            logger.warning(f"Error loading from cache: {e}")
            return None
    
    def set(self, text: str, model_name: str, embedding: np.ndarray) -> None:
        """
        Store embedding in cache.
        
        Args:
            text: Text that was embedded
            model_name: Name of the embedding model
            embedding: Embedding vector
        """
        key = self._get_cache_key(text, model_name)
        file_path = self._get_cache_file_path(key)
        
        try:
            cache_data = {
                "text": text,
                "model_name": model_name,
                "embedding": embedding,
                "timestamp": time.time()
            }
            
            with open(file_path, "wb") as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            logger.warning(f"Error writing to cache: {e}")
    
    def clear(self, max_age_days: Optional[int] = None) -> int:
        """
        Clear expired cache entries.
        
        Args:
            max_age_days: Override default max age
            
        Returns:
            Number of files removed
        """
        if max_age_days is not None:
            max_age_seconds = max_age_days * 24 * 60 * 60
        else:
            max_age_seconds = self.max_age_seconds
        
        removed_count = 0
        current_time = time.time()
        
        for file_name in os.listdir(self.cache_dir):
            if not file_name.endswith(".pkl"):
                continue
            
            file_path = os.path.join(self.cache_dir, file_name)
            file_age = current_time - os.path.getmtime(file_path)
            
            if file_age > max_age_seconds:
                try:
                    os.remove(file_path)
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Error removing cache file {file_path}: {e}")
        
        return removed_count


class Embedder:
    """Class for generating text embeddings."""
    
    def __init__(self, 
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2", 
                 cache_enabled: bool = True,
                 device: Optional[str] = None,
                 batch_size: int = 32):
        """
        Initialize the embedder.
        
        Args:
            model_name: Name of the sentence-transformer model to use
            cache_enabled: Whether to use embedding cache
            device: Device to run the model on (None for auto)
            batch_size: Batch size for embedding generation
        """
        self.model_name = model_name
        self.model = None
        self.device = device
        self.batch_size = batch_size
        
        # Set up cache if enabled
        self.cache_enabled = cache_enabled
        if cache_enabled:
            self.cache = EmbeddingCache()
    
    def load_model(self) -> None:
        """
        Load the embedding model if not already loaded.
        """
        if self.model is None:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name, device=self.device)
                self.embedding_dimension = self.model.get_sentence_embedding_dimension()
                logger.info(f"Model loaded with embedding dimension: {self.embedding_dimension}")
            except Exception as e:
                logger.error(f"Error loading embedding model: {e}")
                raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array with embedding
        """
        # Check if in cache
        if self.cache_enabled:
            cached_embedding = self.cache.get(text, self.model_name)
            if cached_embedding is not None:
                return cached_embedding
        
        # Load model if not loaded
        self.load_model()
        
        # Generate embedding
        embedding = self.model.encode(text, show_progress_bar=False)
        
        # Store in cache
        if self.cache_enabled:
            self.cache.set(text, self.model_name, embedding)
        
        return embedding
    
    def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of numpy arrays with embeddings
        """
        # First check cache for all texts
        embeddings = []
        texts_to_embed = []
        texts_to_embed_indices = []
        
        if self.cache_enabled:
            for i, text in enumerate(texts):
                cached_embedding = self.cache.get(text, self.model_name)
                if cached_embedding is not None:
                    embeddings.append(cached_embedding)
                else:
                    texts_to_embed.append(text)
                    texts_to_embed_indices.append(i)
            
            # If all embeddings were in cache, return them
            if not texts_to_embed:
                return embeddings
        else:
            texts_to_embed = texts
            texts_to_embed_indices = list(range(len(texts)))
            embeddings = [None] * len(texts)
        
        # Load model if not loaded
        self.load_model()
        
        # Generate embeddings in batches
        batch_embeddings = self.model.encode(
            texts_to_embed, 
            batch_size=self.batch_size,
            show_progress_bar=len(texts_to_embed) > 10
        )
        
        # Store in cache and in results
        for i, idx in enumerate(texts_to_embed_indices):
            embedding = batch_embeddings[i]
            
            if self.cache_enabled:
                self.cache.set(texts_to_embed[i], self.model_name, embedding)
            
            embeddings[idx] = embedding
        
        return embeddings
    
    def embed_chunks(self, chunks: List[Chunk]) -> List[Tuple[Chunk, np.ndarray]]:
        """
        Generate embeddings for a list of chunks.
        
        Args:
            chunks: List of Chunk objects
            
        Returns:
            List of tuples containing (chunk, embedding)
        """
        # Extract texts from chunks
        texts = [chunk.text for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.embed_texts(texts)
        
        # Pair chunks with their embeddings
        return list(zip(chunks, embeddings))
    
    @property
    def dimension(self) -> int:
        """Get the dimension of the embeddings."""
        if not hasattr(self, 'embedding_dimension'):
            self.load_model()
        return self.embedding_dimension
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        if self.model is None:
            self.load_model()
            
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "device": self.model.device.type,
            "max_seq_length": self.model.max_seq_length,
        }