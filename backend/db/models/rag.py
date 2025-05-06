"""
RAG-related models for SCIRAG.
"""

import os
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..connection import Base

# Check if we're using SQLite (for testing) or PostgreSQL
DB_URL = os.getenv("DATABASE_URL", "")
IS_SQLITE = "sqlite" in DB_URL

# Import pgvector only if we're not using SQLite
if not IS_SQLITE:
    try:
        from pgvector.sqlalchemy import Vector
    except ImportError:
        # Fallback for environments where pgvector isn't installed
        Vector = None


class RAGCorpus(Base):
    """Model for RAG corpus collections."""
    
    __tablename__ = "rag_corpus"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    documents = relationship("Document", back_populates="corpus", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RAGCorpus(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "document_count": len(self.documents) if self.documents else 0,
        }


class Document(Base):
    """Model for documents in RAG corpus."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    rag_corpus_id = Column(Integer, ForeignKey("rag_corpus.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    corpus = relationship("RAGCorpus", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', corpus_id={self.rag_corpus_id})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "rag_corpus_id": self.rag_corpus_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "chunk_count": len(self.chunks) if self.chunks else 0,
        }


class DocumentChunk(Base):
    """Model for document chunks with embeddings."""
    
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # Use different column types based on database
    if IS_SQLITE:
        # For SQLite testing, store as binary
        embedding = Column(LargeBinary, nullable=True)
    else:
        # For PostgreSQL with pgvector
        embedding = Column(Vector(384), nullable=True)  # Dimension for text-embedding-ada-002 or other 1536-dim model
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_text": self.chunk_text,
            "chunk_index": self.chunk_index,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "has_embedding": self.embedding is not None,
        }