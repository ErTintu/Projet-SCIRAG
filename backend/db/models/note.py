"""
Note-related models for SCIRAG.
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


class Note(Base):
    """Model for personal notes."""
    
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    chunks = relationship("NoteChunk", back_populates="note", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Note(id={self.id}, title='{self.title}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "chunk_count": len(self.chunks) if self.chunks else 0,
        }


class NoteChunk(Base):
    """Model for note chunks with embeddings."""
    
    __tablename__ = "note_chunks"
    
    id = Column(Integer, primary_key=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # Use different column types based on database
    if IS_SQLITE:
        # For SQLite testing, store as binary
        embedding = Column(LargeBinary, nullable=True)
    else:
        # For PostgreSQL with pgvector
        embedding = Column(Vector(384), nullable=True)  # Dimension for text-embedding-ada-002 or other 1536-dim model2
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    note = relationship("Note", back_populates="chunks")
    
    def __repr__(self):
        return f"<NoteChunk(id={self.id}, note_id={self.note_id}, index={self.chunk_index})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "note_id": self.note_id,
            "chunk_text": self.chunk_text,
            "chunk_index": self.chunk_index,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "has_embedding": self.embedding is not None,
        }