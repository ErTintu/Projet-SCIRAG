# backend/tests/test_rag_service.py
"""
Tests for the RAG service module.
"""

import os
import sys
import pytest
import numpy as np
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock, Mock

# Add the parent directory to the path to import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.service import (
    ProcessingTask, ProcessingQueue, ContextBuilder, 
    RAGService, get_rag_service
)
from rag.chunker import Chunk
from rag.store import SearchResult


class TestProcessingTask:
    """Tests for the ProcessingTask class."""
    
    def test_task_creation(self):
        """Test creating a processing task."""
        task = ProcessingTask(
            task_id="123",
            source_id=1,
            source_type="document",
            status="pending"
        )
        
        assert task.task_id == "123"
        assert task.source_id == 1
        assert task.source_type == "document"
        assert task.status == "pending"
        assert task.error is None
        assert task.start_time is None
        assert task.end_time is None
    
    def test_task_to_dict(self):
        """Test converting a task to a dictionary."""
        task = ProcessingTask(
            task_id="123",
            source_id=1,
            source_type="document",
            status="pending"
        )
        
        task_dict = task.to_dict()
        
        assert task_dict["task_id"] == "123"
        assert task_dict["source_id"] == 1
        assert task_dict["source_type"] == "document"
        assert task_dict["status"] == "pending"
        assert task_dict["error"] is None
        assert task_dict["start_time"] is None
        assert task_dict["end_time"] is None


class TestProcessingQueue:
    """Tests for the ProcessingQueue class."""
    
    def test_add_task(self):
        """Test adding a task to the queue."""
        queue = ProcessingQueue()
        queue.start_processing = MagicMock()  # Mock start_processing to avoid starting thread
        
        task_id = queue.add_task(source_id=1, source_type="document")
        
        assert task_id in queue.tasks
        assert task_id in queue.queue
        assert queue.tasks[task_id].source_id == 1
        assert queue.tasks[task_id].source_type == "document"
        assert queue.tasks[task_id].status == "pending"
        assert queue.start_processing.called
    
    def test_get_task(self):
        """Test getting a task by ID."""
        queue = ProcessingQueue()
        queue.start_processing = MagicMock()  # Mock start_processing to avoid starting thread
        
        task_id = queue.add_task(source_id=1, source_type="document")
        task = queue.get_task(task_id)
        
        assert task is not None
        assert task.task_id == task_id
        assert task.source_id == 1
        assert task.source_type == "document"
    
    def test_get_tasks_by_source(self):
        """Test getting tasks by source."""
        queue = ProcessingQueue()
        queue.start_processing = MagicMock()  # Mock start_processing to avoid starting thread
        
        queue.add_task(source_id=1, source_type="document")
        queue.add_task(source_id=1, source_type="document")
        queue.add_task(source_id=2, source_type="document")
        
        tasks = queue.get_tasks_by_source(source_id=1, source_type="document")
        
        assert len(tasks) == 2
        assert all(task.source_id == 1 for task in tasks)
        assert all(task.source_type == "document" for task in tasks)


class TestContextBuilder:
    """Tests for the ContextBuilder class."""
    
    def test_build_context_empty(self):
        """Test building context with no search results."""
        builder = ContextBuilder()
        
        context_text, context_sources = builder.build_context([])
        
        assert context_text == ""
        assert context_sources == []
    
    def test_build_context(self):
        """Test building context from search results."""
        builder = ContextBuilder()
        
        # Create search results
        results = [
            SearchResult(
                chunk=Chunk(
                    text="This is the first chunk",
                    index=0,
                    source_id=1,
                    source_type="document"
                ),
                score=0.95
            ),
            SearchResult(
                chunk=Chunk(
                    text="This is the second chunk",
                    index=1,
                    source_id=2,
                    source_type="document"
                ),
                score=0.85
            )
        ]
        
        context_text, context_sources = builder.build_context(results)
        
        assert "first chunk" in context_text
        assert "second chunk" in context_text
        assert "0.95" in context_text
        assert "0.85" in context_text
        
        assert len(context_sources) == 2
        assert context_sources[0]["source_id"] == 1
        assert context_sources[1]["source_id"] == 2
        assert context_sources[0]["score"] == 0.95
        assert context_sources[1]["score"] == 0.85


class TestRAGService:
    """Tests for the RAGService class."""
    
    @patch('rag.service.ChunkerFactory')
    @patch('rag.service.Embedder')
    @patch('rag.service.ChromaStore')
    def test_init(self, mock_store, mock_embedder, mock_chunker_factory):
        """Test initializing the RAG service."""
        # Mock dependencies
        mock_chunker = MagicMock()
        mock_chunker_factory.get_chunker.return_value = mock_chunker
        
        mock_embedder_instance = MagicMock()
        mock_embedder.return_value = mock_embedder_instance
        
        mock_store_instance = MagicMock()
        mock_store.get_instance.return_value = mock_store_instance
        
        # Initialize service
        service = RAGService()
        
        # Check that dependencies were initialized
        assert service.chunker is mock_chunker
        assert service.embedder is mock_embedder_instance
        assert service.vector_store is mock_store_instance
        assert service.processing_queue is not None
        assert service.context_builder is not None
    
    @patch('rag.service.ChunkerFactory')
    @patch('rag.service.Embedder')
    @patch('rag.service.ChromaStore')
    def test_process_text(self, mock_store, mock_embedder, mock_chunker_factory):
        """Test processing text."""
        # Mock dependencies
        mock_chunker = MagicMock()
        chunks = [
            Chunk(text="Chunk 1", index=0),
            Chunk(text="Chunk 2", index=1)
        ]
        mock_chunker.chunk_text.return_value = chunks
        mock_chunker_factory.get_chunker.return_value = mock_chunker
        
        mock_embedder_instance = MagicMock()
        embeddings = [
            (chunks[0], np.array([0.1, 0.2, 0.3])),
            (chunks[1], np.array([0.4, 0.5, 0.6]))
        ]
        mock_embedder_instance.embed_chunks.return_value = embeddings
        mock_embedder.return_value = mock_embedder_instance
        
        mock_store_instance = MagicMock()
        mock_store.get_instance.return_value = mock_store_instance
        
        # Initialize service
        service = RAGService()
        
        # Process text
        result = service.process_text(
            text="This is a test",
            source_id=1,
            source_type="test"
        )
        
        # Check results
        assert result == embeddings
        mock_chunker.chunk_text.assert_called_once_with(
            text="This is a test",
            source_id=1,
            source_type="test",
            metadata=None
        )
        mock_embedder_instance.embed_chunks.assert_called_once_with(chunks)
    
    @patch('rag.service.ChunkerFactory')
    @patch('rag.service.Embedder')
    @patch('rag.service.ChromaStore')
    def test_search(self, mock_store, mock_embedder, mock_chunker_factory):
        """Test searching for relevant chunks."""
        # Mock dependencies
        mock_chunker = MagicMock()
        mock_chunker_factory.get_chunker.return_value = mock_chunker
        
        mock_embedder_instance = MagicMock()
        query_embedding = np.array([0.1, 0.2, 0.3])
        mock_embedder_instance.embed_text.return_value = query_embedding
        mock_embedder.return_value = mock_embedder_instance
        
        mock_store_instance = MagicMock()
        search_results = [
            SearchResult(
                chunk=Chunk(text="Result 1", index=0),
                score=0.95
            ),
            SearchResult(
                chunk=Chunk(text="Result 2", index=1),
                score=0.85
            )
        ]
        mock_store_instance.search.return_value = search_results
        mock_store.get_instance.return_value = mock_store_instance
        
        # Initialize service
        service = RAGService()
        
        # Search
        results, embedding = service.search(
            query="This is a test query",
            limit=5
        )
        
        # Check results
        assert results == search_results
        assert np.array_equal(embedding, query_embedding)
        mock_embedder_instance.embed_text.assert_called_once_with("This is a test query")
        mock_store_instance.search.assert_called_once_with(
            query_embedding=query_embedding,
            limit=5,
            filter_dict=None
        )
    
    @patch('rag.service.ChunkerFactory')
    @patch('rag.service.Embedder')
    @patch('rag.service.ChromaStore')
    def test_get_context_for_query(self, mock_store, mock_embedder, mock_chunker_factory):
        """Test getting context for a query."""
        # Mock dependencies
        mock_chunker = MagicMock()
        mock_chunker_factory.get_chunker.return_value = mock_chunker
        
        mock_embedder_instance = MagicMock()
        query_embedding = np.array([0.1, 0.2, 0.3])
        mock_embedder_instance.embed_text.return_value = query_embedding
        mock_embedder.return_value = mock_embedder_instance
        
        mock_store_instance = MagicMock()
        search_results = [
            SearchResult(
                chunk=Chunk(text="Result 1", index=0),
                score=0.95
            )
        ]
        mock_store_instance.search.return_value = search_results
        mock_store.get_instance.return_value = mock_store_instance
        
        # Setup mock DB session
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        
        # Mock conversation context results
        context1 = MagicMock()
        context1.context_type = "rag"
        context1.context_id = 1
        
        context2 = MagicMock()
        context2.context_type = "note"
        context2.context_id = 2
        
        mock_filter.all.return_value = [context1, context2]
        
        # Mock documents for RAG corpus
        mock_document = MagicMock()
        mock_document.id = 10
        mock_doc_query = MagicMock()
        mock_db.query.return_value = mock_doc_query
        mock_doc_filter = MagicMock()
        mock_doc_query.filter.return_value = mock_doc_filter
        mock_doc_filter.all.return_value = [mock_document]
        
        # Initialize service with DB session
        service = RAGService(db_session=mock_db)
        
        # Mock context builder
        service.context_builder = MagicMock()
        expected_context = "Test context"
        expected_sources = [{"source": "test"}]
        service.context_builder.build_context.return_value = (expected_context, expected_sources)
        
        # Search for context
        context, sources = service.get_context_for_query(
            query="This is a test query",
            conversation_id=1,
            limit=5
        )
        
        # Check results
        assert context == expected_context
        assert sources == expected_sources
        mock_store_instance.search.assert_called_once()
        service.context_builder.build_context.assert_called_once_with(
            search_results=search_results,
            query="This is a test query"
        )
    
    @patch('rag.service.ChunkerFactory')
    @patch('rag.service.Embedder')
    @patch('rag.service.ChromaStore')
    def test_get_statistics(self, mock_store, mock_embedder, mock_chunker_factory):
        """Test getting RAG system statistics."""
        # Mock dependencies
        mock_chunker = MagicMock()
        mock_chunker_factory.get_chunker.return_value = mock_chunker
        
        mock_embedder_instance = MagicMock()
        mock_embedder_instance.dimension = 384
        mock_embedder.return_value = mock_embedder_instance
        
        mock_store_instance = MagicMock()
        mock_store_instance.get_chunk_count.return_value = 100
        mock_store.get_instance.return_value = mock_store_instance
        
        # Initialize service
        service = RAGService(
            chunker_strategy="paragraph",
            embedding_model="test-model"
        )
        
        # Get statistics
        stats = service.get_statistics()
        
        # Check results
        assert stats["chunk_count"] == 100
        assert stats["chunker_strategy"] == "paragraph"
        assert stats["embedding_model"] == "test-model"
        assert stats["embedding_dimension"] == 384


def test_get_rag_service():
    """Test getting the singleton RAG service instance."""
    # Patch the RAGService class to avoid actual initialization
    with patch('rag.service.RAGService') as mock_service_class:
        mock_service_instance = MagicMock()
        mock_service_class.return_value = mock_service_instance
        
        # Get service instance
        service1 = get_rag_service()
        
        # Should have created a new instance
        assert service1 is mock_service_instance
        mock_service_class.assert_called_once()
        
        # Reset mock to check second call
        mock_service_class.reset_mock()
        
        # Get service instance again
        service2 = get_rag_service()
        
        # Should return the same instance without creating a new one
        assert service2 is mock_service_instance
        mock_service_class.assert_not_called()