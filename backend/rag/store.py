"""
Vector store interface for RAG system.

This module provides an interface to ChromaDB for storing and retrieving 
vector embeddings of document chunks.
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
from datetime import datetime
import threading

# Import ChromaDB
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from .chunker import Chunk

logger = logging.getLogger(__name__)


class SearchResult:
    """Class representing a search result from the vector store."""
    
    def __init__(self, 
                 chunk: Chunk,
                 score: float,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a search result.
        
        Args:
            chunk: The text chunk
            score: Similarity score (higher is better)
            metadata: Additional metadata
        """
        self.chunk = chunk
        self.score = score
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            "chunk": self.chunk.to_dict(),
            "score": self.score,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """Create result from dictionary representation."""
        return cls(
            chunk=Chunk.from_dict(data["chunk"]),
            score=data["score"],
            metadata=data.get("metadata", {})
        )
    
    def __str__(self) -> str:
        """String representation of search result."""
        return f"SearchResult(score={self.score:.4f}, {str(self.chunk)})"


class VectorStore:
    """Abstract base class for vector stores."""
    
    def add_chunks(self, chunks: List[Chunk], embeddings: List[np.ndarray]) -> None:
        """
        Add chunks and their embeddings to the store.
        
        Args:
            chunks: List of chunks to add
            embeddings: List of embeddings corresponding to chunks
        """
        raise NotImplementedError("Subclasses must implement add_chunks")
    
    def search(self, 
               query_embedding: np.ndarray, 
               limit: int = 5,
               filter_dict: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Embedding of the query text
            limit: Maximum number of results to return
            filter_dict: Dictionary of metadata filters
            
        Returns:
            List of SearchResult objects
        """
        raise NotImplementedError("Subclasses must implement search")
    
    def get_chunk_count(self) -> int:
        """Get the total number of chunks in the store."""
        raise NotImplementedError("Subclasses must implement get_chunk_count")
    
    def delete_chunks(self, chunk_ids: List[str]) -> None:
        """
        Delete chunks from the store.
        
        Args:
            chunk_ids: List of chunk IDs to delete
        """
        raise NotImplementedError("Subclasses must implement delete_chunks")
    
    def delete_by_source(self, source_type: str, source_id: Union[int, str]) -> None:
        """
        Delete all chunks from a specific source.
        
        Args:
            source_type: Type of source ("document" or "note")
            source_id: ID of the source
        """
        raise NotImplementedError("Subclasses must implement delete_by_source")
    
    def close(self) -> None:
        """Close the vector store connection."""
        raise NotImplementedError("Subclasses must implement close")


class ChromaStore(VectorStore):
    """ChromaDB implementation of VectorStore."""
    
    _instances = {}
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls, 
                     persist_directory: str = "chroma_data",
                     collection_name: str = "rag_chunks") -> 'ChromaStore':
        """
        Get a singleton instance for a specific collection.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the collection to use
            
        Returns:
            ChromaStore instance
        """
        key = f"{persist_directory}:{collection_name}"
        
        with cls._lock:
            if key not in cls._instances:
                cls._instances[key] = cls(
                    persist_directory=persist_directory,
                    collection_name=collection_name
                )
            
            return cls._instances[key]
    
    def __init__(self, 
                 persist_directory: str = "chroma_data",
                 collection_name: str = "rag_chunks"):
        """
        Initialize the ChromaDB store.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the collection to use
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Create persist directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
            logger.info(f"Using existing ChromaDB collection: {collection_name}")
        except Exception:
            logger.info(f"Creating new ChromaDB collection: {collection_name}")
            self.collection = self.client.create_collection(collection_name)
    
    def add_chunks(self, chunks: List[Chunk], embeddings: List[np.ndarray]) -> None:
        """
        Add chunks and their embeddings to the store.
        
        Args:
            chunks: List of chunks to add
            embeddings: List of embeddings corresponding to chunks
        """
        if not chunks:
            return
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            # Generate a unique ID for the chunk
            chunk_id = f"{chunk.source_type}_{chunk.source_id}_{chunk.index}"
            
            # Add to lists
            ids.append(chunk_id)
            documents.append(chunk.text)
            
            # Prepare metadata
            metadata = {
                "source_type": chunk.source_type or "",
                "source_id": str(chunk.source_id) if chunk.source_id is not None else "",
                "chunk_index": chunk.index,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add any additional metadata from the chunk
            metadata.update(chunk.metadata)
            
            metadatas.append(metadata)
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=[embedding.tolist() for embedding in embeddings],
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"Added {len(chunks)} chunks to ChromaDB collection {self.collection_name}")
        
    def search(self, 
            query_embedding: np.ndarray, 
            limit: int = 5,
            filter_dict: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Embedding of the query text
            limit: Maximum number of results to return
            filter_dict: Dictionary of metadata filters
            
        Returns:
            List of SearchResult objects
        """
        # Convert filter dict to proper ChromaDB format if provided
        where_filter = None
        
        try:
            if filter_dict:
                # Log filter dictionary for debugging
                logger.debug(f"Original filter_dict: {filter_dict}")
                
                # Convert all filter values to strings for consistency
                string_filter = {}
                for key, value in filter_dict.items():
                    if isinstance(value, (list, tuple)):
                        string_filter[key] = [str(v) for v in value]
                    else:
                        string_filter[key] = str(value)
                
                # Handle different filter scenarios
                if "source_type" in string_filter:
                    source_type = string_filter["source_type"]
                    
                    # Case 1: source_type + single source_id
                    if "source_id" in string_filter and not isinstance(string_filter["source_id"], list):
                        where_filter = {
                            "$and": [
                                {"source_type": source_type},
                                {"source_id": string_filter["source_id"]}
                            ]
                        }
                    
                    # Case 2: source_type + list of source_ids
                    elif "source_id" in string_filter and isinstance(string_filter["source_id"], list):
                        source_ids = string_filter["source_id"]
                        
                        # Use $or with multiple $and conditions for multiple IDs
                        or_conditions = []
                        for source_id in source_ids:
                            or_conditions.append({
                                "$and": [
                                    {"source_type": source_type},
                                    {"source_id": source_id}
                                ]
                            })
                        
                        where_filter = {"$or": or_conditions}
                    
                    # Case 3: source_type only
                    else:
                        where_filter = {"source_type": source_type}
                
                # Case 4: Other direct key-value filters
                elif string_filter:
                    # For simple filters, just use the key-value pairs directly
                    where_filter = string_filter
                
                logger.debug(f"Constructed ChromaDB where_filter: {where_filter}")
        except Exception as e:
            logger.error(f"Error constructing ChromaDB filter: {e}")
            # Return empty list on error, not None
            return []
        
        # Perform search with the constructed filter
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=limit,
                where=where_filter
            )
            
            # Process results
            search_results = []
            
            if not results["ids"] or not results["ids"][0]:
                logger.warning("ChromaDB returned empty results")
                return []
            
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                document = results["documents"][0][i]
                distance = results["distances"][0][i] if "distances" in results else 0.0
                
                # Convert similarity score (higher is better)
                # ChromaDB returns distances (lower is better)
                score = 1.0 - distance
                
                # Create chunk
                chunk = Chunk(
                    text=document,
                    index=metadata.get("chunk_index", 0),
                    source_id=metadata.get("source_id"),
                    source_type=metadata.get("source_type"),
                    metadata={k: v for k, v in metadata.items() 
                            if k not in ("source_id", "source_type", "chunk_index")}
                )
                
                # Create search result
                search_result = SearchResult(
                    chunk=chunk,
                    score=score,
                    metadata={"id": doc_id}
                )
                
                search_results.append(search_result)
            
            return search_results
        except Exception as e:
            logger.error(f"ChromaDB search error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Return empty results on error
            return []
    
    def get_chunk_count(self) -> int:
        """Get the total number of chunks in the store."""
        return self.collection.count()
    
    def delete_chunks(self, chunk_ids: List[str]) -> None:
        """
        Delete chunks from the store.
        
        Args:
            chunk_ids: List of chunk IDs to delete
        """
        if not chunk_ids:
            return
        
        self.collection.delete(ids=chunk_ids)
        logger.info(f"Deleted {len(chunk_ids)} chunks from ChromaDB collection {self.collection_name}")
    
    def delete_by_source(self, source_type: str, source_id: Union[int, str]) -> None:
        """
        Delete all chunks from a specific source.
        
        Args:
            source_type: Type of source ("document" or "note")
            source_id: ID of the source
        """
        try:
            # Ensure source_id is a string
            str_source_id = str(source_id)
            
            # Construct filter in proper ChromaDB format
            where_filter = {
                "$and": [
                    {"source_type": source_type},
                    {"source_id": str_source_id}
                ]
            }
            
            # Log filter for debugging
            logger.debug(f"Delete filter: {where_filter}")
            
            # Get items matching the filter
            items = self.collection.get(where=where_filter)
            
            if items and items["ids"]:
                chunk_ids = items["ids"]
                self.delete_chunks(chunk_ids)
                logger.info(f"Deleted {len(chunk_ids)} chunks for {source_type} {source_id}")
            else:
                logger.info(f"No chunks found for {source_type} {source_id}")
        except Exception as e:
            logger.error(f"Error deleting chunks for {source_type} {source_id}: {e}")
        
    def close(self) -> None:
        """Close the ChromaDB connection."""
        # ChromaDB handles this automatically, but we keep the method
        # for compatibility with the VectorStore interface
        logger.info(f"Closed ChromaDB collection {self.collection_name}")
    
    def reset(self) -> None:
        """
        Reset the collection (delete all chunks).
        Warning: This will delete all data in the collection.
        """
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(self.collection_name)
        logger.warning(f"Reset ChromaDB collection {self.collection_name}")