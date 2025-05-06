"""
RAG service for SCIRAG.

This module provides the main service for Retrieval-Augmented Generation (RAG),
integrating the chunker, embedder, and vector store.
"""

import os
import logging
import time
import json
from typing import List, Dict, Any, Optional, Union, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
from uuid import uuid4
import numpy as np

from sqlalchemy.orm import Session

from db.models import (
    RAGCorpus, Document, DocumentChunk, 
    Note, NoteChunk,
    ConversationContext
)
from db.utils import get_or_create

from .chunker import Chunker, Chunk, ChunkerFactory
from .embedder import Embedder
from .store import VectorStore, ChromaStore, SearchResult
from .loader import PDFLoader

logger = logging.getLogger(__name__)


class ProcessingTask:
    """Class representing a document or note processing task."""
    
    def __init__(self, 
                 task_id: str,
                 source_id: Union[int, str],
                 source_type: str,
                 status: str = "pending",
                 error: Optional[str] = None):
        """
        Initialize a processing task.
        
        Args:
            task_id: Unique ID for the task
            source_id: ID of the source document or note
            source_type: Type of source ("document" or "note")
            status: Status of the task ("pending", "processing", "completed", "error")
            error: Error message if status is "error"
        """
        self.task_id = task_id
        self.source_id = source_id
        self.source_type = source_type
        self.status = status
        self.error = error
        self.start_time = None
        self.end_time = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the task to a dictionary."""
        return {
            "task_id": self.task_id,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "status": self.status,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time
        }


class ProcessingQueue:
    """Queue for background processing of documents and notes."""
    
    def __init__(self, max_workers: int = 2):
        """
        Initialize the processing queue.
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.tasks = {}  # task_id -> ProcessingTask
        self.queue = []  # List of task_ids
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processing = False
        self.rag_service = None  # Will be set by RAGService
    
    def add_task(self, source_id: Union[int, str], source_type: str) -> str:
        """
        Add a processing task to the queue.
        
        Args:
            source_id: ID of the source document or note
            source_type: Type of source ("document" or "note")
            
        Returns:
            Task ID
        """
        task_id = str(uuid4())
        task = ProcessingTask(
            task_id=task_id,
            source_id=source_id,
            source_type=source_type
        )
        
        with self.lock:
            self.tasks[task_id] = task
            self.queue.append(task_id)
        
        # Start processing if not already running
        if not self.processing:
            self.start_processing()
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[ProcessingTask]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            ProcessingTask or None if not found
        """
        return self.tasks.get(task_id)
    
    def get_tasks_by_source(self, source_id: Union[int, str], source_type: str) -> List[ProcessingTask]:
        """
        Get all tasks for a specific source.
        
        Args:
            source_id: ID of the source
            source_type: Type of source
            
        Returns:
            List of ProcessingTask objects
        """
        return [
            task for task in self.tasks.values()
            if task.source_id == source_id and task.source_type == source_type
        ]
    
    def start_processing(self) -> None:
        """Start background processing of the queue."""
        if self.processing:
            return
        
        self.processing = True
        self.executor.submit(self._process_queue)
    
    def _process_queue(self) -> None:
        """Process tasks in the queue (run in background thread)."""
        while True:
            task_id = None
            
            # Get next task from queue
            with self.lock:
                if not self.queue:
                    self.processing = False
                    break
                
                task_id = self.queue.pop(0)
                task = self.tasks[task_id]
                task.status = "processing"
                task.start_time = time.time()
            
            # Process the task
            try:
                if task.source_type == "document":
                    self.rag_service.process_document(task.source_id)
                elif task.source_type == "note":
                    self.rag_service.process_note(task.source_id)
                else:
                    raise ValueError(f"Unknown source type: {task.source_type}")
                
                # Update task status
                with self.lock:
                    task.status = "completed"
                    task.end_time = time.time()
                
                logger.info(f"Completed processing task {task_id}: {task.source_type} {task.source_id}")
                
            except Exception as e:
                logger.error(f"Error processing task {task_id}: {e}")
                
                # Update task status
                with self.lock:
                    task.status = "error"
                    task.error = str(e)
                    task.end_time = time.time()


class ContextBuilder:
    """Builder for constructing context for LLM prompts from search results."""
    
    def __init__(self, max_tokens: int = 2000):
        """
        Initialize the context builder.
        
        Args:
            max_tokens: Maximum tokens for the context
        """
        self.max_tokens = max_tokens
    
    def build_context(self, 
                      search_results: List[SearchResult],
                      query: str = "") -> Tuple[str, List[Dict[str, Any]]]:
        """
        Build context from search results.
        
        Args:
            search_results: List of search results
            query: Original query text
            
        Returns:
            Tuple of (context_text, context_sources)
        """
        if not search_results:
            return "", []
        
        context_parts = []
        context_sources = []
        
        # Process results in order of relevance
        for result in search_results:
            chunk = result.chunk
            score = result.score
            
            # Add source information
            source_type = chunk.source_type or "unknown"
            source_id = chunk.source_id or "unknown"
            
            # Format the chunk text
            chunk_text = chunk.text.strip()
            
            # Add to context parts
            context_parts.append(f"[Content from {source_type} {source_id}, relevance: {score:.2f}]\n{chunk_text}")
            
            # Add to context sources
            context_sources.append({
                "source_type": source_type,
                "source_id": source_id,
                "chunk_index": chunk.index,
                "score": score
            })
        
        # Join context parts
        context_text = "\n\n".join(context_parts)
        
        # If context is too long, truncate it
        # This is a simple truncation strategy; more sophisticated strategies
        # could be implemented based on token counts
        if len(context_text) > self.max_tokens * 4:  # Rough estimate of 4 chars per token
            context_text = context_text[:self.max_tokens * 4] + "..."
        
        return context_text, context_sources


class RAGService:
    """Main service for Retrieval-Augmented Generation."""
    
    def __init__(self, 
                 db_session: Optional[Session] = None,
                 chunker_strategy: str = "paragraph",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 persist_directory: str = "chroma_data",
                 collection_name: str = "rag_chunks"):
        """
        Initialize the RAG service.
        
        Args:
            db_session: SQLAlchemy database session (optional)
            chunker_strategy: Strategy for chunking
            embedding_model: Model for embeddings
            persist_directory: Directory for ChromaDB storage
            collection_name: Name of the ChromaDB collection
        """
        self.db_session = db_session
        self.chunker_strategy = chunker_strategy
        self.embedding_model = embedding_model
        
        # Initialize components
        self.chunker = ChunkerFactory.get_chunker(strategy=chunker_strategy)
        self.embedder = Embedder(model_name=embedding_model)
        self.vector_store = ChromaStore.get_instance(
            persist_directory=persist_directory,
            collection_name=collection_name
        )
        
        # Initialize processing queue
        self.processing_queue = ProcessingQueue()
        self.processing_queue.rag_service = self
        
        # Initialize context builder
        self.context_builder = ContextBuilder()
    
    def set_db_session(self, db_session: Session) -> None:
        """
        Set the database session.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
    
    def process_text(self, 
                    text: str, 
                    source_id: Optional[Union[int, str]], 
                    source_type: Optional[str],
                    metadata: Optional[Dict[str, Any]] = None) -> List[Tuple[Chunk, np.ndarray]]:
        """
        Process text into chunks and embeddings.
        """
        # Chunk the text
        chunks = self.chunker.chunk_text(
            text=text,
            source_id=source_id,
            source_type=source_type,
            metadata=metadata
        )
        
        if not chunks:
            logger.warning(f"No chunks generated for {source_type} {source_id}")
            return []
        
        logger.info(f"Generated {len(chunks)} chunks for {source_type} {source_id}")
        
        try:
            # Generate embeddings
            chunk_embeddings = self.embedder.embed_chunks(chunks)
            logger.info(f"Generated {len(chunk_embeddings)} embeddings for {source_type} {source_id}")
            
            # Vérifiez que les embeddings ne sont pas None
            valid_embeddings = []
            for chunk, embedding in chunk_embeddings:
                if embedding is not None and len(embedding) > 0:
                    valid_embeddings.append((chunk, embedding))
                else:
                    logger.warning(f"Empty or None embedding for chunk: {chunk.text[:50]}...")
            
            logger.info(f"Valid embeddings: {len(valid_embeddings)}/{len(chunk_embeddings)}")
            return valid_embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def process_document(self, document_id: int) -> None:
        """Process a document: extract text, chunk, embed, and store."""
        if not self.db_session:
            raise ValueError("Database session not set")
        
        # Get document from database
        document = self.db_session.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Extract text from PDF
        try:
            pdf_data = PDFLoader.extract_text_from_pdf(document.file_path)
            full_text = pdf_data["full_text"]
            
            # Process the text
            chunk_embeddings = self.process_text(
                text=full_text,
                source_id=document_id,
                source_type="document",
                metadata={
                    "filename": document.filename,
                    "file_type": document.file_type,
                    "corpus_id": document.rag_corpus_id
                }
            )
            
            # Delete any existing chunks for this document
            self.vector_store.delete_by_source("document", document_id)
            
            # Add to vector store
            chunks, embeddings = zip(*chunk_embeddings) if chunk_embeddings else ([], [])
            self.vector_store.add_chunks(list(chunks), list(embeddings))
            
            # Store chunks in database
            self.db_session.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).delete()
            
            for i, (chunk, embedding) in enumerate(chunk_embeddings):
                # Convertir l'embedding en format approprié si nécessaire
                embedding_binary = embedding.tobytes() if isinstance(embedding, np.ndarray) else embedding
                
                db_chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_text=chunk.text,
                    chunk_index=i,
                    embedding=embedding_binary
                )
                # Important: Définir explicitement has_embedding à True
                # Ceci corrige le problème
                db_chunk.has_embedding = True
                self.db_session.add(db_chunk)
            
            self.db_session.commit()
            
            logger.info(f"Successfully processed document {document_id}: {len(chunk_embeddings)} chunks")
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            self.db_session.rollback()
            raise

    def process_note(self, note_id: int) -> None:
        """Process a note: chunk, embed, and store."""
        if not self.db_session:
            raise ValueError("Database session not set")
        
        # Get note from database
        logger.info(f"Processing note {note_id}")
        note = self.db_session.query(Note).filter(Note.id == note_id).first()
        if not note:
            raise ValueError(f"Note {note_id} not found")
        
        try:
            # Process the text
            logger.info(f"Processing note {note_id}: {note.title}")
            chunk_embeddings = self.process_text(
                text=note.content,
                source_id=note_id,
                source_type="note",
                metadata={
                    "title": note.title
                }
            )
            logger.info(f"Generated {len(chunk_embeddings)} chunk-embedding pairs")
            
            # Delete any existing chunks for this note
            self.vector_store.delete_by_source("note", note_id)
            
            # Add to vector store
            chunks, embeddings = zip(*chunk_embeddings) if chunk_embeddings else ([], [])
            logger.info(f"Adding {len(chunks)} chunks to vector store")
            self.vector_store.add_chunks(list(chunks), list(embeddings))
            
            # Store chunks in database
            logger.info(f"Deleting existing chunks for note {note_id}")
            self.db_session.query(NoteChunk).filter(
                NoteChunk.note_id == note_id
            ).delete()
            
            logger.info(f"Adding {len(chunk_embeddings)} chunks to database")
            for i, (chunk, embedding) in enumerate(chunk_embeddings):
                # Convertir l'embedding en format approprié si nécessaire
                embedding_binary = embedding.tobytes() if isinstance(embedding, np.ndarray) else embedding
                
                db_chunk = NoteChunk(
                    note_id=note_id,
                    chunk_text=chunk.text,
                    chunk_index=i,
                    embedding=embedding_binary
                )
                # Important: Définir explicitement has_embedding à True
                # Ceci corrige le problème
                db_chunk.has_embedding = True
                self.db_session.add(db_chunk)
            
            self.db_session.commit()
            
            logger.info(f"Successfully processed note {note_id}: {len(chunk_embeddings)} chunks")
            
        except Exception as e:
            logger.error(f"Error processing note {note_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.db_session.rollback()
            raise

    def queue_document_processing(self, document_id: int) -> str:
        """
        Queue a document for background processing.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Task ID
        """
        return self.processing_queue.add_task(document_id, "document")
    
    def queue_note_processing(self, note_id: int) -> str:
        """
        Queue a note for background processing.
        
        Args:
            note_id: ID of the note
            
        Returns:
            Task ID
        """
        return self.processing_queue.add_task(note_id, "note")
    
    def get_processing_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a processing task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Dictionary with task status
        """
        task = self.processing_queue.get_task(task_id)
        if not task:
            return {"status": "not_found"}
        
        return task.to_dict()
    
    def search(self, 
            query: str, 
            limit: int = 5,
            filter_dict: Optional[Dict[str, Any]] = None) -> Tuple[List[SearchResult], np.ndarray]:
        """
        Search for relevant chunks.
        
        Args:
            query: Query text
            limit: Maximum number of results
            filter_dict: Filters for the search
            
        Returns:
            Tuple of (search_results, query_embedding)
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)
        
        try:
            # Search vector store
            search_results = self.vector_store.search(
                query_embedding=query_embedding,
                limit=limit,
                filter_dict=filter_dict
            )
            
            # Assurez-vous que search_results est toujours une liste, même si None est renvoyé
            if search_results is None:
                logger.warning("Vector store search returned None, using empty list instead")
                search_results = []
                
            return search_results, query_embedding
        except Exception as e:
            logger.error(f"Error in search: {e}")
            # En cas d'erreur, retourner une liste vide
            return [], query_embedding
    
    def get_context_for_query(self, 
                            query: str,
                            conversation_id: Optional[int] = None,
                            limit: int = 5) -> Tuple[str, List[Dict[str, Any]]]:
        """Get context for a query based on conversation settings."""
        if not self.db_session:
            raise ValueError("Database session not set")
        
        logger.info(f"Getting context for query: '{query}' (conversation_id={conversation_id})")
        
        all_results = []
        active_contexts = []
        
        # Si conversation_id est fourni, récupérer les contextes actifs
        if conversation_id:
            active_contexts = self.db_session.query(ConversationContext).filter(
                ConversationContext.conversation_id == conversation_id,
                ConversationContext.is_active == True
            ).all()
            
            logger.info(f"Found {len(active_contexts)} active contexts")
        
        if active_contexts:
            # Séparer les RAGs et les notes
            rag_ids = []
            note_ids = []
            
            for ctx in active_contexts:
                if ctx.context_type == "rag":
                    rag_ids.append(ctx.context_id)
                elif ctx.context_type == "note":
                    note_ids.append(ctx.context_id)
            
            logger.info(f"Active RAG IDs: {rag_ids}")
            logger.info(f"Active Note IDs: {note_ids}")
            
            # Traiter séparément chaque note active
            for note_id in note_ids:
                try:
                    # Recherche exacte avec un filtre spécifique
                    note_results, _ = self.search(
                        query=query,
                        limit=limit,
                        filter_dict={
                            "source_type": "note",
                            "source_id": str(note_id)
                        }
                    )
                    
                    if note_results:
                        logger.info(f"Found {len(note_results)} results for note {note_id}")
                        all_results.extend(note_results)
                except Exception as e:
                    logger.error(f"Error searching note {note_id}: {e}")
            
            # Traiter séparément chaque RAG actif
            for rag_id in rag_ids:
                try:
                    # Récupérer tous les documents du corpus
                    documents = self.db_session.query(Document).filter(
                        Document.rag_corpus_id == rag_id
                    ).all()
                    
                    for doc in documents:
                        # Recherche exacte avec un filtre spécifique
                        doc_results, _ = self.search(
                            query=query,
                            limit=limit // len(documents) if documents else limit,
                            filter_dict={
                                "source_type": "document",
                                "source_id": str(doc.id)
                            }
                        )
                        
                        if doc_results:
                            logger.info(f"Found {len(doc_results)} results for document {doc.id}")
                            all_results.extend(doc_results)
                except Exception as e:
                    logger.error(f"Error searching RAG {rag_id}: {e}")
        
        else:
            logger.info("No active contexts found, performing general search")
            # Recherche générale sans filtre
            general_results, _ = self.search(query=query, limit=limit)
            all_results = general_results
        
        # Trier les résultats par score et limiter
        all_results.sort(key=lambda x: x.score, reverse=True)
        search_results = all_results[:limit]
        
        # Construire le contexte
        context_text, sources = self.context_builder.build_context(
            search_results=search_results,
            query=query
        )
        
        logger.info(f"Built context from {len(search_results)} results")
        
        return context_text, sources
    
    def get_available_sources(self, conversation_id: Optional[int] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get available sources for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Dictionary of sources by type
        """
        if not self.db_session:
            raise ValueError("Database session not set")
        
        result = {
            "rag_corpus": [],
            "notes": []
        }
        
        # Get all RAG corpus
        rag_corpora = self.db_session.query(RAGCorpus).all()
        for corpus in rag_corpora:
            # Count documents
            document_count = self.db_session.query(Document).filter(
                Document.rag_corpus_id == corpus.id
            ).count()
            
            # Check if active in this conversation
            is_active = False
            if conversation_id:
                context = self.db_session.query(ConversationContext).filter(
                    ConversationContext.conversation_id == conversation_id,
                    ConversationContext.context_type == "rag",
                    ConversationContext.context_id == corpus.id,
                    ConversationContext.is_active == True
                ).first()
                
                is_active = context is not None
            
            result["rag_corpus"].append({
                "id": corpus.id,
                "name": corpus.name,
                "description": corpus.description,
                "document_count": document_count,
                "is_active": is_active
            })
        
        # Get all notes
        notes = self.db_session.query(Note).all()
        for note in notes:
            # Check if active in this conversation
            is_active = False
            if conversation_id:
                context = self.db_session.query(ConversationContext).filter(
                    ConversationContext.conversation_id == conversation_id,
                    ConversationContext.context_type == "note",
                    ConversationContext.context_id == note.id,
                    ConversationContext.is_active == True
                ).first()
                
                is_active = context is not None
            
            result["notes"].append({
                "id": note.id,
                "title": note.title,
                "is_active": is_active
            })
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the RAG system.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "chunk_count": self.vector_store.get_chunk_count(),
            "chunker_strategy": self.chunker_strategy,
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedder.dimension,
            "processing_queue_length": len(self.processing_queue.queue)
        }
        
        # Add database statistics if available
        if self.db_session:
            stats.update({
                "rag_corpus_count": self.db_session.query(RAGCorpus).count(),
                "document_count": self.db_session.query(Document).count(),
                "note_count": self.db_session.query(Note).count(),
            })
        
        return stats
    
    def close(self) -> None:
        """Close all resources."""
        self.vector_store.close()


# Create RAG service singleton instance
_rag_service_instance = None
_rag_service_lock = threading.Lock()

def get_rag_service(db_session: Optional[Session] = None, **kwargs) -> RAGService:
    """
    Get the singleton RAG service instance.
    
    Args:
        db_session: SQLAlchemy database session
        **kwargs: Additional parameters for RAGService initialization
        
    Returns:
        RAGService instance
    """
    global _rag_service_instance
    
    with _rag_service_lock:
        if _rag_service_instance is None:
            logger.info("Initializing RAG service")
            _rag_service_instance = RAGService(db_session=db_session, **kwargs)
        elif db_session and _rag_service_instance.db_session != db_session:
            _rag_service_instance.set_db_session(db_session)
    
    return _rag_service_instance