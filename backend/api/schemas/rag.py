"""
Pydantic schemas for RAG-related API endpoints.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class RAGCorpusBase(BaseModel):
    """Base schema for RAG corpus data."""
    name: str = Field(..., description="Corpus name")
    description: Optional[str] = Field(None, description="Corpus description")


class RAGCorpusCreate(RAGCorpusBase):
    """Schema for creating a new RAG corpus."""
    pass


class RAGCorpusUpdate(BaseModel):
    """Schema for updating a RAG corpus."""
    name: Optional[str] = Field(None, description="New corpus name")
    description: Optional[str] = Field(None, description="New corpus description")


class DocumentBase(BaseModel):
    """Base schema for document data."""
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Path to stored file")
    file_type: str = Field(..., description="File type (e.g., pdf, txt)")


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    rag_corpus_id: int = Field(..., description="ID of the RAG corpus")


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: int
    rag_corpus_id: int
    created_at: datetime
    chunk_count: int = Field(0, description="Number of chunks in the document")
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class DocumentChunkBase(BaseModel):
    """Base schema for document chunk data."""
    chunk_text: str = Field(..., description="Text content of the chunk")
    chunk_index: int = Field(..., description="Index position of the chunk")


class DocumentChunkCreate(DocumentChunkBase):
    """Schema for creating a new document chunk."""
    document_id: int = Field(..., description="ID of the parent document")


class DocumentChunkResponse(DocumentChunkBase):
    """Schema for document chunk response."""
    id: int
    document_id: int
    created_at: datetime
    has_embedding: bool = Field(False, description="Whether the chunk has an embedding")
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class RAGCorpusResponse(RAGCorpusBase):
    """Schema for RAG corpus response."""
    id: int
    created_at: datetime
    updated_at: datetime
    document_count: int = Field(0, description="Number of documents in the corpus")
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class RAGCorpusDetailResponse(RAGCorpusResponse):
    """Schema for detailed RAG corpus response including documents."""
    documents: List[DocumentResponse] = []
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class UploadDocumentResponse(BaseModel):
    """Schema for document upload response."""
    corpus_id: int
    document_id: int
    filename: str
    success: bool
    message: str